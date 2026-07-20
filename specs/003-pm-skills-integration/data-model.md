# Data Model: PM Skills Integration

**Date**: 2026-07-11
**Feature**: PM Skills Integration (003)
**关联**: `spec.md`（需求）、`architecture.md`（接口规范）

---

## Overview

本特征在**不新增主数据实体**的前提下，复用现有 `SkillContract` 和 `ModuleEntry`，并新增**PmSkillsMapping**配置实体用于管理 pm-skills 到 SkillContract 的映射关系。所有新增结构都可从现有模型派生，保证数据不扩散。

---

## Existing Entities（复用，不修改）

### SkillContract

统一技能注册表条目，覆盖 native PM skills 和 pm-skills。

```typescript
interface SkillContract {
  id: string;                                  // 唯一，如 "pm-skills/prd-generation"
  name: string;                                // 展示名
  description: string;                         // 供 Agent 检索 & 用户选择
  category: 'analysis' | 'generation' | 'extraction' | 'workflow';
  inputSchema?: Record<string, unknown>;       // JSON Schema（可选）
  outputContract: Record<string, unknown>;     // JSON Schema，必须可落回 ModuleEntry
  methodRef?: string;                          // 可执行 Python 类全路径（可选）
  methodologyRef?: string;                     // 关联 SKILL.md 路径（可选）
  invocation: 'explicit' | 'autonomous' | 'both';
  requiresConfirm: boolean;                    // 写操作必须为 true
}
```

**角色**：一切技能的注册目标。pm-skills 通过 PmSkillsMapping 映射到此处。

### ModuleEntry

统一数据模型（existing）。Key attributes: id, projectId, moduleType, title, content, data, metadata, version.

---

## New Entities（支撑结构）

### PmSkillsMapping（pm-skills 映射配置）

配置 pm-skills 命令到 SkillContract 的映射关系。

```typescript
interface PmSkillsMapping {
  id: string;                    // 唯一映射 ID
  commandId: string;            // pm-skills 命令 ID（如 "write-prd"）
  skillContractId: string;        // 指向 SkillContract.id
  version: string;              // pm-skills 版本号
  methodologyRef: string;         // SKILL.md 文件路径
  outputContractId?: string;      // 输出契约 ID（可选）
  enabled: boolean;              // 是否启用
  createdAt: number;
  updatedAt: number;
}
```

**存储**：配置表 `pm_pm_skills_mappings`，管理员通过 UI 维护。

### PmSkillsVersion（版本跟踪）

跟踪 pm-skills 版本信息。

```typescript
interface PmSkillsVersion {
  commandId: string;              // 命令 ID
  version: string;              // 版本号
  methodologyHash: string;       // SKILL.md 内容哈希
  updatedAt: number;             // 更新时间
}
```

**存储**：配置表 `pm_pm_skills_versions`。

---

## Relationships

```
PmSkillsMapping
  ├── commandId → pm-skills 命令标识
  ├── skillContractId → SkillContract.id（通用模块）
  └── outputContractId → outputContract（可选）

SkillContract（通用模块，复用）
  ├── id: "pm-skills/<command-id>"
  ├── methodologyRef: "pm-skills/<plugin>/<skill>/SKILL.md"
  └── invocation: "explicit" | "autonomous" | "both"

ModuleEntry（真相源，复用）
  └── 产物经 outputContract 校验后写回此处
```

---

## Validation Rules

- `PmSkillsMapping.commandId` MUST be unique across all mappings.
- `PmSkillsMapping.skillContractId` MUST reference an existing `SkillContract.id`.
- `PmSkillsMapping.version` MUST match the version in `PmSkillsVersion`.
- `SkillContract.methodologyRef` MUST point to an existing SKILL.md file.
- All operations MUST carry `projectId` and MUST NOT be queryable across projects (Constitution Principle IV).

---

## State Transitions

1. **导入 pm-skills**：扫描 `pm-skills/` 目录 → 为每个 SKILL.md 创建 `PmSkillsMapping` → 生成对应 `SkillContract` → 注册到统一注册表。
2. **工作流绑定（Timbal 嵌入式）**：管理员在 Open WebUI 工作流配置中定义 Timbal Workflow 步骤 → 每个步骤引用 `skillContractId` → Timbal 在 Open WebUI 后端进程中执行（`import timbal`，NOT `timbal start`）。
3. **显式调用**：用户输入 `/pm-<id>` → 系统通过 `PmSkillsMapping` 查找 `skillContractId` → 调用对应 `SkillContract` → 执行 skill → 产物经 `outputContract` 校验 → 落库 `ModuleEntry`。
4. **自主调用**：Agent 根据上下文选择相关 pm-skills → 通过 `PmSkillsMapping` 解析 → 执行并返回结果。
5. **Timbal 工作流执行（嵌入式）**：
   - Timbal Workflow 在 Open WebUI 后端进程中运行（`await workflow().collect()`）
   - 按步骤顺序执行 → 每步通过 `skillContractId` 调用对应 skill
   - 输出经 `outputContract` 校验 → 下一步接收上一步的输出作为输入
   - 最终产物落库 `ModuleEntry`
