# 基于 Open WebUI 改造 PM 工具台

## Context

【溯源：用户目标「基于open-webui 做一个产品经理工具台」；规划设计路径「D:\project\pm-workspace\open-pm-webui\docs\prd」；底座「https://docs.openwebui.com/」；可参考「https://deepwiki.com/open-webui/open-webui」；且说明「可以大幅度改代码」】

当前仓库是 Open WebUI 底座，实际技术栈与 PRD 文档中写的 Agent Native/React/Drizzle 有明显差异：

- 当前 `package.json` 显示项目为 `open-webui`，前端为 SvelteKit/Vite/Svelte 5，脚本包含 `dev`、`build`、`check`、`test:frontend`。【溯源：`package.json` lines 1-23, 24-51】
- 当前依赖已有 TipTap、CodeMirror、Chart.js、xlsx、marked、mermaid、sql.js、uuid 等，可复用做文档编辑、表格、图表、导入导出。【溯源：`package.json` lines 67-156】
- PRD 定位为「面向产品经理的 AI 工作流平台」，并强调「手动操作为主路径，AI 为增强辅助」。【溯源：`PM-Workflow-Platform-PRD-v1.0.md` lines 14-17】
- PRD 核心原则包括「手动优先」「AI 增强」「项目隔离」「版本可控」「关系可追溯」「流程建议」。【溯源：`PM-Workflow-Platform-PRD-v1.0.md` lines 18-27】
- PRD 原规划技术约束为 Agent Native、React、SQLite/PostgreSQL、Drizzle，但这与 Open WebUI 底座不一致。【溯源：`PM-Workflow-Platform-PRD-v1.0.md` lines 29-36；`package.json` lines 24-51】
- 实施计划原定 Phase 1 是项目创建/切换、数据隔离、AI 对话、项目列表；Phase 2 是 PRD 编辑、检查、参数清单闭环。【溯源：`PM-Workflow-Platform-Implementation-Plan-v1.0.md` lines 172-220】
- API 文档定义了项目、工作流、版本、关系、需求、竞品、路线图、PRD、参数、测试用例等模块的 action 命名范围。【溯源：`PM-Workflow-Platform-API-Design-v1.0.md` lines 10-45】
- DB 文档定义核心表：projects、project_templates、versions、workflows、entities、relations，以及 requirements 等业务表。【溯源：`PM-Workflow-Platform-DB-Design-v1.0.md` lines 10-180】

因此，���次改造不新建 React/Agent Native 项目，而是在 Open WebUI 现有 SvelteKit + Python 后端架构内落地 PM 工具台。PRD 中的「Action」概念会映射为 Open WebUI 后端 API 路由与前端服务调用；PRD 中的数据模型会映射为 Open WebUI 后端模型/迁移/Schema，而不是照搬 Drizzle。

## Approach

1. **做架构映射与边界收敛**
   - 将 PRD 的 Agent Native Actions 映射为 Open WebUI 后端 REST API。
   - 将 PRD 的 React routes/components 映射为 SvelteKit routes/components。
   - 保留 Open WebUI 现有用户、会话、模型、聊天、文件与权限基础能力，避免重复造 AI 对话底座。
   - 不引入 React/Drizzle/Agent Native，除非后续明确要彻底重构底座。

2. **Phase 1：PM 工作台壳与项目隔离**
   - 新增 PM 工具台入口，例如 `/pm` 或工作区侧边栏入口。
   - 实现项目列表、项目创建、项目详情、项目切换。
   - 后端新增 PM 项目数据模型，至少覆盖：`projects`、`project_templates`、`workflows`、基础 `documents` 或 Open WebUI 现有文档引用关系。
   - 所有 PM 业务数据强制带 `project_id`，前端请求与后端查询都以当前项目为上下文。
   - 创建内置项目模板：通用产品、PRD 项目、竞品分析项目，对应默认模块和默认工作流。

3. **Phase 1：AI 辅助入口复用 Open WebUI 能力**
   - 在 PM 工具台内嵌 AI 辅助面板，复用 Open WebUI 当前模型/聊天能力。
   - AI 面板只做「建议/生成草稿/检查结果」，所有写入动作必须由用户确认，符合 PRD 的手动优先原则。
   - PM 上下文传入 AI 时包含：当前项目、当前模块、选中文档/需求/参数项、用户选中文本。
   - 不先做复杂 Agent 编排，先实现可追溯的 prompt 模板和手动应用结果。

4. **Phase 2：PRD 核心闭环**
   - 新增 PRD 文档列表与编辑页。
   - 优先复用项目已有 TipTap/Markdown/CodeMirror 能力，根据现有代码选择最少侵入方案。
   - 支持 PRD 章节结构、目录导航、保存、版本快照。
   - 实现基础 PRD 检查：必填章节、空内容、术语不一致、未关联需求/参数等规则；AI 检查作为增强项。
   - 生成的 AI 建议需要展示来源上下文和原文片段，用户确认后再写入。

5. **Phase 2：需求与参数清单**
   - 实现需求池表格：标题、描述、来源、优先级、状态、标签、模块、功能。
   - 支持 xlsx/CSV 导入需求，利用当前依赖中的 `xlsx` 做前端或后端解析。
   - 实现参数清单表格：模块、功能、字段名、类型、必填、默认值、枚举、说明、来源 PRD 位置。
   - 支持从 PRD 选中文本手动创建参数项；AI 提取只生成候选项，用户确认后入库。

6. **Phase 3：版本、追溯与工作流看板**
   - 实现版本快照：项目级快照、PRD 文档版本、差异对比。
   - 实现实体关系：需求-PRD章节-功能-参数-测试用例之间的可追溯关系。
   - 实现建议性工作流看板：步骤状态可手动改、可跳过、可自定义，不强制流程顺序。
   - 追溯关系由用户手动建立为主，AI 只做候选建议并标记置信度。

7. **Phase 4：扩展模块按业务价值逐步落地**
   - 竞品分析、路线图、测试用例、会议纪要、风险、交付物、验收、问题闭环、复盘、培训、手册、FAQ、宣讲材料等模块按 PRD 模块清单逐步实现。
   - 每个模块先做手动 CRUD 与项目隔离，再做 AI 辅助。
   - 避免一次性铺开 28 个模块导致数据模型和交互不可控。

8. **验收与验证策略**
   - 每个阶段完成后运行前端检查：`npm run check`。
   - 涉及前端单测时运行：`npm run test:frontend`。
   - 涉及构建兼容时运行：`npm run build`。
   - 涉及 Python 后端时按项目现有方式补充后端 lint/test；如现有 lint 过重或历史问题较多，需要记录非本次引入的问题。
   - 手工验收路径：创建项目 → 切换项目 → 新建 PRD → 编辑保存 → 新建需求 → 新建参数 → 建立关联 → AI 生成建议 → 用户确认应用 → 创建版本快照 → 查看差异。

## Key Files

- `docs/prd/PM-Workflow-Platform-PRD-v1.0.md`
  - 作为产品范围、原则、模块定义和验收依据，不直接实现其中的 React/Agent Native 技术栈。

- `docs/prd/PM-Workflow-Platform-API-Design-v1.0.md`
  - 作为 API 能力清单来源，将 action 命名映射到 Open WebUI 后端路由。

- `docs/prd/PM-Workflow-Platform-DB-Design-v1.0.md`
  - 作为业务数据模型来源，将 Drizzle 表结构转换为 Open WebUI 后端实际 ORM/迁移/Schema。

- `docs/prd/PM-Workflow-Platform-Implementation-Plan-v1.0.md`
  - 作为阶段拆分依据，但阶段任务需要适配 Open WebUI 当前架构。

- `package.json`
  - 用于确认前端技术栈、脚本和可复用依赖；后续验证会使用 `check`、`test:frontend`、`build` 等脚本。

- `src/`
  - 新增或改造 PM 工具台前端页面、组件、状态与 API client。

- `backend/`
  - 新增 PM 项目、需求、PRD、参数、版本、关系等后端模型与 API。

- `static/` 或项目现有文件存储目录
  - 若 PRD/附件/导入文件需要落地文件系统，优先复用 Open WebUI 已有文件管理方式；若不能复用，再新增 PM 项目目录。

## Risks & Open Questions

1. **技术栈冲突风险**
   - PRD 写的是 React + Agent Native + Drizzle，但用户目标是基于 Open WebUI。计划默认以 Open WebUI 架构为准，不照搬 PRD 技术栈。
   - 【溯源：`PM-Workflow-Platform-PRD-v1.0.md` lines 29-36；`package.json` lines 24-51】

2. **范围过大风险**
   - PRD 覆盖完整 PM 生命周期和 20+ 模块，一次性实现会影响稳定性。建议先做 Phase 1 + Phase 2 的 MVP，再逐步扩展。
   - 【溯源：`PM-Workflow-Platform-API-Design-v1.0.md` lines 15-45；`PM-Workflow-Platform-Implementation-Plan-v1.0.md` lines 172-220】

3. **Open WebUI 后端模型未在本轮深入读取**
   - 本计划已确认前端栈和 PRD 范围，但尚未细读 Open WebUI 的后端 DB/路由约定。进入 Build 前应先定位现有 `backend/` 中的模型、迁移、鉴权和路由写法，再做最小一致实现。

4. **AI 写入边界必须谨慎**
   - 根据 PRD「手动优先」「AI 增强」原则，AI 不应直接修改需求、PRD、参数、版本等核心数据；必须先展示候选结果，用户确认后写入。
   - 【溯源：`PM-Workflow-Platform-PRD-v1.0.md` lines 16-27】

5. **用户需确认 MVP 优先级**
   - 默认建议 MVP 顺序为：项目隔离 → PRD 编辑 → 需求池 → 参数清单 → AI 辅助 → 版本快照 → 追溯关系。
   - 若业务上更看重竞品、原型走查或测试用例，应调整 Phase 2/3 的优先级。