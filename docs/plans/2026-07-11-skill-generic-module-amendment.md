# 宪法修订提案：技能即通用模块（Skill-as-Generic-Module）

- **Status**: PROPOSED（待 24h 评审，宪法 §Amendment Procedure #4）
- **Target Version**: 1.2.0（MINOR：既有原则 VI 的实质性扩展）
- **Proposed**: 2026-07-11 14:02 (GMT+8)
- **Ratify After**: 2026-07-12 14:02 (GMT+8) — 24-hour review window
- **Owner**: 聂鹏
- **Source**: 设计准则 `design-principles.md` §2「技能即通用模块」经 brainstorming 验证（specs/002-agent-data-platform/）

---

## 1. 变更摘要

将「技能即通用模块（Skill-as-Generic-Module）」从**设计准则**提升为宪法**原则 VI 的硬约束（HARD CONSTRAINT / 写死）**，并明确：

- 一切 Agent 能力 = `SkillContract` 通用模块 或 `pm_*` Tool，禁止散落硬编码。
- 技能必须声明 `id/name/description/outputContract/invocation/requiresConfirm`。
- 双调用：显式（`/pm-<id>` / 面板）＋ 自主（Agent 自选且必回显 skillId + 理由）。
- Timbal 仅作**内嵌确定性流水线引擎**（collect→clean→standardize），**不取代** Open WebUI 原生编排（Tools/Skills/Pipelines/Knowledge）。

## 2. 影响分析

| 维度 | 影响 |
|------|------|
| 受影响原则 | VI. Agent Platform Capabilities（Skill Layer 重写 + 新增 Workflow Engine 约束） |
| 受影响模板 | plan / spec / tasks 模板的 Constitution Check 需引用新约束 |
| 不受影响 | 原则 I–V；技术栈 §Agent Framework（保持 Open WebUI 原生） |
| 路径说明 | 宪法 §Amendment Procedure 写 `.orgii/plans/`，该目录本仓库不存在（疑为 `.specify/plans/` 或 `docs/plans/` 笔误）。本提案依仓库实际结构置于 `docs/plans/`。 |

## 3. 目标文本（ratification 后直接替换原则 VI 对应部分）

### 3.1 原则 VI — Skill Layer 重写为 HARD CONSTRAINT

> 替换原 VI 中 "**Skill Layer**: High-frequency PM workflows MUST be encapsulated as Skills ..." 整条为：

- **Skill Layer — Skills are Generic Modules (HARD CONSTRAINT)**: Every PM capability exposed to agents MUST be a self-contained, reusable `SkillContract` module — NOT hardcoded logic bound to a single PM module or feature. Each skill MUST declare: `id` (kebab-case), `name`, `description`, `outputContract` (JSON Schema, MUST be persistable to `ModuleEntry`), `invocation` (explicit | autonomous | both), and `requiresConfirm` (MUST be true for any write). Skills are invoked two ways: (a) **explicit** via `/pm-<id>` command or skill-palette selection — deterministic, no agent guessing; (b) **autonomous** — the agent self-selects the best-matching skill from the unified registry and MUST echo the chosen `skillId` plus a one-line reason. All skills (including pm-skills methodology references) MUST be registered in the unified skill registry. No new agent capability may be implemented as scattered hardcoded logic; it MUST be either a `SkillContract` generic module or a `pm_*` Tool.

### 3.2 新增约束（置于原则 VI 末尾）

- **Deterministic Pipeline Engine**: Data pipelines (collect → clean → standardize) MAY use an embedded workflow library (e.g., Timbal) strictly as a Python library for deterministic, idempotent processing. This does NOT replace Open WebUI native agent orchestration (Tools / Skills / Pipelines / Knowledge), which remains the sole orchestration layer per Technology Stack §Agent Framework.

## 4. 不做的事（Out-of-Scope，防扩散）

- 不引入独立 Timbal 编排微服务（违反 §Agent Framework）。
- 不将 68 个 `SKILL.md` 全部转写为 Python 类。
- 不修改原则 I–V。
- 不改变 `project_id` 隔离与人工确认门（原则 III / IV）。

## 5. Follow-up TODOs

- TODO(SKILL_PATH): 宪法 Code Organization 写 `backend/skills/pm_*.py`，实际代码在 `backend/open_webui/pm/skills/` —— 路径后续统一（不在本修订范围）。
- TODO(RATIFY): 2026-07-12 14:02 评审期结束后，将 §3 目标文本应用至 `.specify/memory/constitution.md` 原则 VI，并更新顶部 Sync Impact Report（版本 1.1.0 → 1.2.0、Last Amended 日期）。

## 6. 合规声明

本提案与 `design-principles.md` §0 IN-SCOPE 完全一致；不引入任何 OUT-OF-SCOPE 能力。修订后，后续所有 AI Agent 相关开发将被「技能即通用模块」硬约束锁死，从根上防止能力扩散。
