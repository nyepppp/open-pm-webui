# Data Model: Agent 与数据平台

**Date**: 2026-07-11
**Feature**: Agent & Data Platform (002-agent-data-platform)
**关联**: `spec.md`（需求）、`architecture.md`（接口规范）

---

## Overview

本特征在**不新增主数据实体**的前提下，复用现有 `ModuleEntry` 作为唯一真相源，并新增少量**支撑性结构**用于技能注册、标准化视图、调用记录与知识分块。所有新增结构都可从 `ModuleEntry` 派生，保证数据不扩散。

---

## Existing Entities（复用，不修改）

### ModuleEntry

统一数据模型，覆盖 requirement / parameter / spec / module / feature 等 `moduleType`，带 `project_id` 隔离、版本、关联。

```typescript
interface ModuleEntry {
  id: string;
  projectId: string;
  moduleType: ModuleType;
  title: string;
  status: string;
  priority?: string;
  content?: string;
  data?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  createdAt: number;
  updatedAt: number;
  version?: number;
  currentVersionNumber?: string;
}
```

**角色**：一切产物的最终落库目标。技能产出经 `outputContract` 校验后写回此处。

---

## New Entities（支撑结构）

### SkillContract（技能注册表条目）

通用技能模块的标准化契约。既描述可执行技能，也描述方法论技能。

```typescript
interface SkillContract {
  id: string;                                  // 唯一，如 "prd-generation"
  name: string;
  description: string;                         // 供 Agent 检索 & 用户选择
  category: 'analysis' | 'generation' | 'extraction' | 'workflow';
  inputSchema?: Record<string, unknown>;      // JSON Schema（可选）
  outputContract: Record<string, unknown>;    // JSON Schema，必须可落回 ModuleEntry
  methodRef?: string;                         // 可执行 Python 类全路径（可选）
  methodologyRef?: string;                    // 关联 SKILL.md 路径（可选）
  invocation: 'explicit' | 'autonomous' | 'both';
  requiresConfirm: boolean;                    // 写操作必须为 true
}
```

**存储**：统一注册表（扩展 `backend/open_webui/pm/skills/__init__.py` 的 registry）。

### NormalizedEntry（标准化视图）

Timbal 工作流对 `ModuleEntry` 采集→清洗→标准化后的产物。**不独立持久化主数据**，可作为缓存/视图存在。

```typescript
interface NormalizedEntry {
  entryId: string;            // 指向 ModuleEntry.id
  projectId: string;
  moduleType: ModuleType;
  standardizedFields: Record<string, unknown>;  // 清洗后归一字段
  version: string;            // 对应 ModuleEntry.currentVersionNumber
  normalizedAt: number;       // 标准化时间戳（用于幂等判断）
}
```

**特性**：幂等（同一 entry+version 多次标准化结果一致）；失败时不写，回退到原始 `ModuleEntry`。

### SkillInvocation（技能调用记录）

每次技能执行的审计轨迹，支撑可观测与透明性（自主调用必须回显 reason）。

```typescript
interface SkillInvocation {
  id: string;
  projectId: string;
  skillId: string;            // 指向 SkillContract.id
  mode: 'explicit' | 'autonomous';
  chosenReason?: string;      // 自主调用时的选择理由（必填 when autonomous）
  inputArgs?: Record<string, unknown>;
  outputRef?: string;         // 落库的 ModuleEntry.id 或 NormalizedEntry.entryId
  confirmedBy?: string;       // 确认人（写操作）
  status: 'pending' | 'confirmed' | 'rejected' | 'failed';
  createdAt: number;
}
```

### KnowledgeChunk（知识分块）

文档类 `ModuleEntry` 切分后用于 RAG 的块，必须带来源引用。

```typescript
interface KnowledgeChunk {
  chunkId: string;
  entryId: string;            // 指向 ModuleEntry.id
  projectId: string;
  moduleType: ModuleType;     // prd / meeting / competitor ...
  title: string;
  content: string;
  version: string;
  source: string;             // 引用：/pm/{projectId}/{moduleType}/{entryId}
}
```

---

## Relationships

```
SkillContract (通用模块)
  ├── methodRef → Python 类（可执行技能）
  ├── methodologyRef → SKILL.md（方法论技能）
  └── invocation: explicit | autonomous | both

SkillInvocation
  ├── skillId → SkillContract.id
  └── outputRef → ModuleEntry.id（落库产物）

NormalizedEntry
  └── entryId → ModuleEntry.id（标准化视图，幂等）

KnowledgeChunk
  └── entryId → ModuleEntry.id（文档分块，带来源引用）

ModuleEntry（真相源，复用）
  └── projectId 隔离 + version + relations（既有）
```

---

## Validation Rules

- `SkillContract.outputContract` MUST be a valid JSON Schema and MUST describe a shape persistable to `ModuleEntry` (title/content/data/metadata).
- `SkillContract.requiresConfirm` MUST be `true` for any skill whose output writes to `ModuleEntry`.
- `SkillInvocation.mode === 'autonomous'` MUST have non-empty `chosenReason`.
- `KnowledgeChunk.source` MUST be reconstructable to the exact `ModuleEntry` (projectId + moduleType + entryId).
- `NormalizedEntry` is keyed by `(entryId, version)`; re-standardizing same key MUST be idempotent.
- All entities MUST carry `projectId` and MUST NOT be queryable across projects (Constitution Principle IV).

---

## State Transitions

1. **技能注册**：`SkillContract` 加入注册表 → 可被显式/自主调用。
2. **显式调用**：用户输入 `/pm-<id>` → `intent.py` 解析 → skill 运行 → `outputContract` 校验 → `SkillInvocation(pending)` → 用户确认 → 落库 `ModuleEntry` → `SkillInvocation(confirmed)`.
3. **自主调用**：Pipeline 注入注册表摘要 → Agent 选 skill + 写 `chosenReason` → 同显式后续流程。
4. **按需标准化**：Agent 请求 → Timbal 唤醒 → `ModuleEntry` → `NormalizedEntry`（幂等）→ 双轨供给。
5. **知识同步**：`ModuleEntry`(文档类) → 切分 → `KnowledgeChunk`（带 `source`）→ 入 Knowledge 供 RAG。
