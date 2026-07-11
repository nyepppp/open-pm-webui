# 设计准则：Agent 与数据平台（Agent & Data Platform Design Principles）

**Version**: 1.0.0 (draft)
**Status**: 待评审
**Created**: 2026-07-11
**Owner**: 聂鹏
**关联文档**: `roadmap.md`（几步走）、`architecture.md`（架构）、`spec.md` + `data-model.md`（需求）

> 本文档用于规范 open-pm-webui 后续 AI 相关开发的**设计准则**，确保 Agent 集成、数据流水线、技能体系在同一套原则下推进，**防止范围无序扩散**。它是对 `.specify/memory/constitution.md` 原则 VI（Agent Platform Capabilities）的**细化与约束**，不修改宪法正文。

---

## 0. 目的与范围边界（防扩散）

### IN-SCOPE（本期必须收敛在这）
- **技能通用模块 + 双调用**：skill 作为自包含可复用模块，支持「用户指定 / Agent 自主选择」两种调用。
- **Timbal 内嵌为工作流引擎**：只承接确定性数据流水线（采集 → 清洗 → 标准化），Agent 编排仍走 Open WebUI 原生。
- **pm-skills 方法论融合**：68 个 `SKILL.md` 作为方法论知识层 + 高价值技能配 JSON Schema 输出契约；LLM 进 prompt 自由、出 schema 严格。
- **数据流水线按需拉取**：Agent 调用时触发标准化，非实时常驻。
- **双轨供给**：结构数据走 `pm_*` Tools 精查，文档类走 Knowledge RAG 语义召回。
- **统一数据底座**：复用现有 `ModuleEntry`（project_id 隔离 + 版本 + 关联），产物必须落回该结构。

### OUT-OF-SCOPE（显式延期，禁止本期扩散）
- 独立 Timbal 编排微服务 / 替换 Open WebUI 原生 Agent（违反原则 VI）。
- 实时事件驱动流水线（每次存盘触发）。
- 将 68 个 `SKILL.md` 全部转为可执行 Python 类。
- 跨项目 Agent、外部模型市场、自训练/微调模型。
- 任何不落回 `ModuleEntry` 结构的自由文本产物（无规范化则不允许入库）。

---

## 1. 四大根决策（与既有规划对齐）

1. **Timbal 定位**：内嵌为工作流引擎，只做确定性流水线；Agent 编排仍走 Open WebUI 原生（宪法原则 VI 保持不变）。
2. **pm-skills 形态**：`SKILL.md` 方法论知识库 + 高价值技能配输出契约；方法论负责「怎么想」，契约负责「必须回到 ModuleEntry 落库」。
3. **流水线触发**：Agent 调用时**按需拉取 + 标准化**（非实时常驻、非定时批处理）。
4. **数据终点**：**双轨**——结构数据（需求/参数）走 `pm_*` Tools 精确直取；文档类（PRD/会议/竞品）走 Knowledge RAG 语义召回。

---

## 2. 核心准则：技能即通用模块（Skill-as-Generic-Module）

> 这是本期最关键的约束，任何 Agent 相关开发必须遵循。

- **通用性**：一个 skill 是**自包含、可复用的能力模块**，不绑定某个具体 PM 模块/功能；它可被需求、PRD、参数等任意模块复用。
- **标准化契约**：每个 skill 必须声明
  - `id` / `name` / `description`（供 Agent 检索与用户选择）
  - `inputSchema`（可选，参数化输入）
  - `outputContract`（JSON Schema，约束产物结构，**必须能落回 ModuleEntry**）
  - `systemPrompt` 或方法论引用（`SKILL.md`）
  - `invocation`：`explicit` / `autonomous` / `both`
- **双调用（Dual Invocation）**：
  - **用户指定（显式）**：用户输入 `/pm-<skill>` 或从技能面板选择 → 确定性强调用。
  - **Agent 自主选择（自主）**：Pipeline/Agent 依据对话上下文 + 技能注册表，自动选择最匹配的 skill 并调用；**必须声明所选 skill 及理由**。
- **中心注册**：所有 skill（含 pm-skills 方法论）登记于统一注册表（扩展 `backend/open_webui/pm/skills/__init__.py` 的 registry + `SKILL.md` 目录）。
- **不扩散**：新增 skill 必须复用通用模块骨架，不得为单次特性写一次性硬编码逻辑。

---

## 3. 与既有宪法的对齐

- **原则 I（Manual-First）**：skill 产出一律为建议态，需人工确认（已有 `requires_confirm=True` 机制）。
- **原则 III（AI-Assisted, Human-Confirmed）**：所有 skill 写操作必须走 action 确认门。
- **原则 IV（Data Isolation & Traceability）**：skill 永远在 `project_id` 作用域内；跨项目禁止；关联记入 relations 表。
- **原则 V（Version-Controlled）**：skill 产生的文档类产物沿用现有版本快照机制。
- **原则 VI（Agent Platform Capabilities）**：本文档是其**细化约束**，不推翻；后续若需提升为宪法原则，走 24h 评审流程。

---

## 4. 设计约束（给后续 AI 开发）

1. 任何新 Agent 能力 = 新增一个「通用 skill 模块」或「`pm_*` Tool」，不得散落逻辑。
2. 数据流水线 = Timbal Workflow，确定性、可测试、幂等；失败回退到「未标准化原始数据 + 提示」。
3. 产物必须回写 `ModuleEntry`；非结构化产出需先经 `outputContract` 归一。
4. 接口版本独立于 PM API（宪法 Data Compatibility）；Tool schema 与 Skill 契约各自演进。
5. RAG 响应必须带来源引用（满足原则 VI RAG 要求）。

---

## 5. 后续动作

- 第 2 节「技能即通用模块」已提升为**宪法修订提案（PROPOSED）**：见 `docs/plans/2026-07-11-skill-generic-module-amendment.md`。走 24h 评审流程（宪法 §Amendment Procedure），ratify after **2026-07-12 14:02**；评审通过后应用至原则 VI，版本升至 1.2.0，并将「技能即通用模块」写为 HARD CONSTRAINT（写死）。（注：宪法原写 `.orgii/plans/`，本仓库无该目录，依实际结构置于 `docs/plans/`。）
- 实施顺序见 `roadmap.md`；模块设计与接口见 `architecture.md`；可编码需求见 `spec.md` + `data-model.md`。
