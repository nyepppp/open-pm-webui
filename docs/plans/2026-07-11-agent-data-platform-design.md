# Design: Agent 与数据平台（open-pm-webui）

**Date**: 2026-07-11
**Status**: Validated (brainstorming complete)
**Author**: 聂鹏
**Process**: Brainstorming → 4 root decisions confirmed → design sections presented → this consolidated doc
**Detailed specs**: `specs/002-agent-data-platform/` (design-principles / roadmap / architecture / spec / data-model)

---

## 1. 背景与目标 (Context & Goal)

open-pm-webui 基于 Open WebUI 开发，已沉淀 PM 工作台（表单、富文本、流程图、架构图、SPEC 等模块），底层是统一的 `ModuleEntry` 数据模型。下一步要把 Agent 接进来，让用户无感地调用后台流程，并**规范产品数据**。

目标不是"再做一个 Agent 框架"，而是：在守住既有宪法（原则 VI Agent Platform Capabilities）的前提下，把外部能力（timbal.ai 工作流、pm-skills 方法论）以可控方式融入，让数据能沉淀、提取、思考、使用。

---

## 2. 关键决策（已与用户确认）

| # | 决策点 | 结论 |
|---|--------|------|
| 1 | Timbal 定位 | 内嵌为**工作流引擎**，只做确定性流水线；Agent 编排仍走 Open WebUI 原生 |
| 2 | pm-skills 形态 | 68 个 `SKILL.md` 作**方法论知识层 + 高价值技能配输出契约**（LLM 进 prompt 自由、出 schema 严格） |
| 3 | 流水线触发 | Agent 调用时**按需拉取 + 标准化**（非实时常驻、非定时批处理） |
| 4 | 数据终点 | **双轨**：结构数据走 `pm_*` Tools 精查，文档类走 Knowledge RAG 语义召回 |

---

## 3. 架构 (Architecture)

分层（自上而下 = 一次 Agent 调用生命周期）：

1. **用户触点**：PM 工作台（已完成）+ Open WebUI 对话框，共享同一 `project_id` → Agent 自动感知"当前项目"。
2. **编排层**：Open WebUI 原生 Agent + Pipeline，自动注入 `project_id` / `tool_ids` / `knowledge_ids` / `skill_registry_summary`。不引入 Timbal 编排。
3. **技能层**：通用 skill 模块（registry）+ pm-skills 方法论（SKILL.md）。
4. **工作流引擎**：Timbal（内嵌，仅确定性脏活：采集→清洗→标准化）。
5. **双轨供给**：`pm_*` Tools（精查）+ Knowledge（RAG）。
6. **数据底座**：`ModuleEntry`（project_id 隔离 + 版本 + 关联），一切真相源。

---

## 4. 核心组件 (Components)

**4.1 技能即通用模块（SkillContract）** — 本期最关键约束。
每个 skill 是 `SkillContract`：`id / name / description / category / inputSchema? / outputContract / methodRef? / methodologyRef? / invocation / requiresConfirm`。
- `invocation`: `explicit`（用户 `/pm-<id>`）| `autonomous`（Agent 自主选择）| `both`。
- 自主调用**必须**回显所选 skill id + 理由（透明性）。
- 复用现有 `skills/base.py` 的 `BaseSkill` 骨架，新增 `outputContract` + `invocation` 即符合。

**4.2 数据流水线（Timbal Workflow）** — 按需唤醒，一次性跑完：采集 → 清洗 → 标准化为 `NormalizedEntry` → 双轨输出 → 产物经 `outputContract` 落回 `ModuleEntry`。

**4.3 双轨供给** — 结构数据经 `pm_*` Tools 精查；文档类切分为 `KnowledgeChunk`（带 `source` 引用）入 Knowledge 供 RAG，响应须带来源引用。

---

## 5. 数据流 (Data Flow)

```
Agent 请求
 → Pipeline 注入 project_id
 → 唤醒 Timbal（采集 project 的 ModuleEntry）
 → 清洗 + 标准化 → NormalizedEntry（幂等）
 → 双轨：结构→pm_* Tools；文档→KnowledgeChunk
 → Agent 基于规范化数据推理
 → 产物经 outputContract 校验 → action 确认门(requires_confirm)
 → 落回 ModuleEntry
```

---

## 6. 错误处理 (Error Handling)

- **标准化失败**：回退到原始 `ModuleEntry` + 提示，**绝不**返回半成品标准化数据。
- **outputContract 校验失败**：返回错误给用户，允许重试或手动编辑，不落库。
- **无 project_id**（对话未绑定项目）：Agent 走 general 模式，需要项目上下文的 skill 禁用。
- **AI 服务不可用**：skill 降级为 manual-only / general 模式（原则 I Manual-First）。
- **跨项目访问**：API 层拒绝（原则 IV），绝不返回他项目数据。

---

## 7. 测试策略 (Testing)

- **技能双调用**：显式 `/pm-<id>` 确定性命中 registry；自主模式 100% 回显 skill id + 理由。
- **流水线幂等**：同一 project 重复触发，NormalizedEntry 一致。
- **双轨供给**：RAG 答案 100% 带 `source` 引用；Tool 精查返回结构符合 schema。
- **确认门**：所有写操作经 `requires_confirm` 才落库（原则 III）。
- **隔离**：0 跨项目数据泄漏（API 层断言）。
- **防扩散**：本期新增 Agent 能力 100% 为 `SkillContract` 或 `pm_*` Tool（无散落逻辑）。

---

## 8. 分阶段路线图 (Roadmap)

| 阶段 | 优先级 | 目标 | 依赖 |
|------|--------|------|------|
| P0 技能基座 | P0 | 通用 skill 模块 + registry + 双调用 | — |
| P1 数据流水线 | P1 | Timbal 内嵌 + 按需标准化 + 双轨骨架 | P0 |
| P2 方法论融合 | P2 | 68 SKILL.md 入库 + Top-10 输出契约 | P0,P1 |
| P3 双轨供给 | P2 | Tools 精查 + Knowledge RAG + Pipeline 注入 | P1 |
| P4 自主编排 | P3 | Agent 串联多 skill + 确认门 + 可观测 | P2,P3 |

P2 / P3 可并行。详细交付物与退出标准见 `roadmap.md`。

---

## 9. 防扩散边界 (Scope)

**IN-SCOPE**：通用 skill 模块 + 双调用；Timbal 内嵌；pm-skills 方法论 + 契约；按需标准化；双轨供给；复用 `ModuleEntry`。
**OUT-OF-SCOPE（显式延期）**：独立 Timbal 微服务；实时事件驱动；68 个全转 Python；跨项目 Agent；外部模型市场；自训练模型；不落回 ModuleEntry 的自由文本产物。

---

## 10. 关联文档 (References)

- `specs/002-agent-data-platform/design-principles.md` — 设计准则（含 IN/OUT-OF-SCOPE）
- `specs/002-agent-data-platform/roadmap.md` — 几步走（分阶段交付物 + 防扩散检查单）
- `specs/002-agent-data-platform/architecture.md` — 分层架构 + 接口规范
- `specs/002-agent-data-platform/spec.md` — Feature Specification（用户故事 + FR + SC）
- `specs/002-agent-data-platform/data-model.md` — 数据模型（SkillContract / NormalizedEntry / SkillInvocation / KnowledgeChunk）
- `.specify/memory/constitution.md` — 原则 VI Agent Platform Capabilities（本文档为其细化约束，未修改正文）
