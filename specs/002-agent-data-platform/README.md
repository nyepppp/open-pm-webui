# 002 · Agent 与数据平台 — AI 阅读入口手册（Reading Manifest）

> **给 AI coding agent 的第一份文件。** 你在动手前，必须按下方「阅读顺序」读完标注为 `[MUST]` 的文件。
> 本手册只做导航，不含设计内容本身。所有路径均相对仓库根 `open-pm-webui/`。

---

## 0. 一句话背景

在 Open WebUI 之上建 PM 工作台，把已完成的表单/富文本/流程图/架构图数据**规范化**，并打通 Agent，使其能**沉淀、提取、思考、使用**产品数据。本轮不写业务代码之前，先由这套文档锁定设计与边界。

---

## 1. 阅读顺序（严格按序，先读约束再读实现）

| 序 | 文件 | 级别 | 读它是为了回答 |
|----|------|------|----------------|
| ① | `.specify/memory/constitution.md` | **[MUST]** | 项目宪法。不可违反的原则（Manual-First / AI-Assisted Human-Confirmed / 数据隔离可追溯 / 原则 VI 技能层）。**任何设计冲突以此为准。** |
| ② | `specs/002-agent-data-platform/design-principles.md` | **[MUST]** | 总闸。四大根决策 + `IN-SCOPE / OUT-OF-SCOPE` 红线 + 「技能即通用模块」硬约束。**防扩散看这里。** |
| ③ | `specs/002-agent-data-platform/spec.md` | **[MUST]** | 需求规格。用户故事 + FR-001~012 + 成功标准 + 边界。**要做什么看这里。** |
| ④ | `specs/002-agent-data-platform/data-model.md` | **[MUST]** | 数据模型。复用 `ModuleEntry`，新增 `SkillContract / NormalizedEntry / SkillInvocation / KnowledgeChunk`。**数据形状看这里。** |
| ⑤ | `specs/002-agent-data-platform/architecture.md` | [SHOULD] | 分层架构 + 双调用流程 + 按需流水线生命周期 + 接口规范。**怎么搭看这里。** |
| ⑥ | `specs/002-agent-data-platform/phase-tasks.md` | **[MUST]** | P0–P4 共 17+ 个 coding-ready task，每个带规格级接口/验收/依赖/OUT。**动手的清单看这里。** |
| ⑦ | `specs/002-agent-data-platform/roadmap.md` | [SHOULD] | 分阶段路线图与依赖矩阵。**先做哪步、依赖谁看这里。** |

---

## 2. 待批准治理文档（生效前不得据其改宪法正文）

| 文件 | 状态 | 说明 |
|------|------|------|
| `docs/plans/2026-07-11-agent-data-platform-design.md` | 已验证 | brainstorming 整合设计文档（架构/组件/数据流/错误处理/测试五要素），是 002 的对外入口。 |
| `docs/plans/2026-07-11-skill-generic-module-amendment.md` | **PROPOSED（24h 评审中）** | 把「技能即通用模块」提为宪法原则 VI 的 HARD CONSTRAINT。**未 ratify 前，宪法正文仍是旧版；以提案 §3 目标文本为将来方向，但当前不得据此改 constitution.md。** |

---

## 3. 代码锚点（改动必须对齐这些既有文件，禁止另起炉灶）

| 路径 | 角色 | 对应 task |
|------|------|-----------|
| `backend/open_webui/pm/skills/base.py` | 技能基类 `BaseSkill`，将扩展 `outputContract / invocation` | P0-T1 |
| `backend/open_webui/pm/skills/*.py` | 现有技能（prd_generation / requirement_analysis / requirement_review） | P0-T1/T2 |
| `backend/open_webui/pm/intent.py` | 关键词意图识别 | P0-T3 |
| `backend/open_webui/pm/tools.py` | `pm_*` 精查工具 | P3-T1 |
| `backend/open_webui/pm/actions.py` | 动作层 | P0-T4 确认门 |
| `backend/open_webui/pm/tool_functions.py` | 工具函数注册 | P0-T2 注册表 |

---

## 4. 动手前的硬性 CHECK（每个 task 开工前自查）

- [ ] 已读 ①②③④⑥，且本 task 不违反 `design-principles.md` 的 **OUT-OF-SCOPE**（禁止：独立 Timbal 微服务 / 实时事件驱动 / 68 个 SKILL.md 全转 Python / 散落硬编码能力）。
- [ ] 新增/改动的产物**能回落到 `ModuleEntry` 结构**（见 data-model.md 的 `outputContract`）。
- [ ] Timbal 仅以 `import` 内嵌（`from timbal import Workflow` / `.step()` / `.collect()`），**禁止 `timbal start` 起独立服务**。
- [ ] 术语不混：本项目 `SkillContract`（通用模块）≠ Timbal 自带的 `Skills/Tools/Agents`。
- [ ] 技能能力二选一实现：`SkillContract` 通用模块 或 `pm_*` Tool；双调用（显式 `/pm-<id>` + Agent 自主自选须回显 `skillId + 理由`）。

---

## 5. 推荐起点

零业务依赖、最稳的落地起点：**`phase-tasks.md` 的 P0-T1 与 P0-T2**（BaseSkill 升级 + 统一注册表）。从这两个 task 的「规格级接口 + 验收标准」直接开写。
