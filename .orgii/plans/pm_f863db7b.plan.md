# PM 工作台功能完善与打通计划

## Context

当前 PM 工作台已有雏形，但多个核心功能尚未完成或存在断层：

- **基础信息功能**：各模块（PRD、需求、参数、测试用例、风险、竞品、路线图、会议、验收、FAQ、产品架构、原型、排期）的差异化编辑器已存在，但部分模块的字段与 PRD 定义不一致，且缺乏模块专属的基础信息展示。
- **版本功能**：已有项目级版本（`pm_version`）和条目级版本（`pm_entry_version`），但两者未打通；版本对比 UI 已存在但对比 API 未实现；版本与基础信息的关联（如某版本包含哪些条目变更）缺失。
- **溯源功能**：已有关系图（`PMTraceabilityGraph`）和关联 API，但溯源链路未与版本流转关联，也缺乏合理性自动判定。
- **Agent 功能**：已有 `PMAgentChatPanel` 和 `agentChatStore`，但仅支持通用对话，未对接 OpenWebUI 的 Agent 基础设施，也未实现 PRD 生成、需求分析等 Skill 的专用工作流。
- **数据模型**：当前使用统一的 `pm_entry` 表存储所有模块条目，通过 `module_type` 区分。PRD 期望的是各模块有独立的表结构（如 `requirements`、`parameters`、`testcases` 等），但当前实现为了快速迭代使用了统一表+JSON `data` 字段的方式。

## Approach

### Phase 1: 模块基础信息对齐（1-2 天）

1. **统一模块字段定义**：在 `src/lib/apis/pm/types.ts` 中完善各模块的专属接口，确保与 PRD 的 DB Design 一致。
2. **完善模块配置**：在 `[module]/+page.svelte` 的 `moduleConfig` 中，为每个模块补充完整的 `tableColumns` 和 `formFields`，与 PRD 定义的字段一一对应。
3. **基础信息面板**：在模块编辑页面增加"基础信息"侧边栏/折叠面板，展示条目的元数据（创建时间、更新时间、版本号、状态、优先级、关联模块等）。
4. **模块图标与分类对齐**：确保 `+page.svelte` 中的 `moduleGroups` 与 PRD 的 5 大分类（规划、需求设计、项目管理、落地验收、复盘迭代、赋能协作）一致。

### Phase 2: 版本功能打通与留存对照（2-3 天）

1. **项目版本与条目版本关联**：
   - 在创建项目版本时，自动快照当前项目下所有条目的最新版本号，存入 `pm_version` 表的 `meta` 字段或新建关联表。
   - 在版本详情页展示该版本包含的条目清单及其当时的版本号。
2. **版本对比 API 实现**：
   - 实现 `GET /projects/{project_id}/versions/compare` 接口，对比两个项目版本之间的条目差异（新增、修改、删除）。
   - 实现条目级版本对比的完整后端逻辑（当前前端 UI 已存在，但后端 diff 算法未实现）。
3. **版本留存对照 UI**：
   - 在版本管理页面（`versions/+page.svelte`）增加"版本快照详情"展开面板，展示该版本下的所有条目状态。
   - 在条目编辑页面的版本历史下拉框中，显示该条目所属的项目版本信息。

### Phase 3: 溯源功能与版本流转关联（2-3 天）

1. **溯源链路增强**：
   - 在 `relations` 表中增加 `version_snapshot` 字段（JSON），记录建立关联时双方的版本号。
   - 在追溯图（`PMTraceabilityGraph`）中展示关联建立时的版本上下文。
2. **合理性自动判定**：
   - 实现后端规则引擎，对关联关系进行自动校验：
     - `contains`：检查实体 A 的版本是否包含实体 B 的创建版本。
     - `references`：检查引用关系是否指向存在的条目。
     - `derives`：检查派生关系是否符合模块间的逻辑（如需求 → 参数 → 测试用例）。
     - `conflicts`：检查冲突双方是否处于同一项目版本。
   - 在关系图和追溯面板中，用颜色/图标标记"合理"、"可疑"、"冲突"的关联。
3. **版本流转追溯**：
   - 在条目详情页增加"版本流转时间线"，展示该条目从创建到当前的所有版本变更，以及每次变更时关联的其他条目版本变化。

### Phase 4: Agent 功能通用模块与工作流（3-4 天）

1. **通用 Agent 工具模块**：
   - 创建 `src/lib/components/pm/PMAgentTool.svelte`：通用 Agent 调用组件，支持传入 Skill ID、上下文参数、回调处理。
   - 创建 `src/lib/apis/pm/agent.ts`：统一封装对后端 Agent API 的调用，包括 `agent.chat`、`agent.skill.call`、`agent.status`。
2. **对接 OpenWebUI Agent**：
   - 复用 OpenWebUI 已有的模型选择和聊天基础设施（`generateOpenAIChatCompletion`、`modelsStore`）。
   - 在 `agentChatStore` 中增加 Skill 路由逻辑：根据用户输入的意图，自动选择对应的 Skill（PRD 生成、需求分析、竞品调研等）。
3. **Skill 工作流实现**：
   - **PRD 生成 Skill**：调用后端 `agent/skill/prd-generation`，传入项目上下文，生成 PRD 大纲 → 用户确认 → 逐章填充 → 保存为 PRD 条目。
   - **需求分析 Skill**：分析当前项目需求，给出分类、优先级、冲突检测建议。
   - **参数提取 Skill**：从 PRD 内容中自动提取参数清单。
   - **测试用例生成 Skill**：根据需求和参数生成测试用例。
   - **版本对比 Skill**：对比两个版本并生成变更摘要。
   - **关联建议 Skill**：分析项目条目，建议合理的关联关系。
4. **Agent 动作执行**：
   - 解析 Agent 返回的 `action` JSON 块，在前端执行对应的操作（创建条目、更新内容、创建关联等），执行前需用户确认。

### Phase 5: 完善与验收（2-3 天）

1. **工作流页面完善**：将当前 mock 数据的 `workflow/+page.svelte` 改为真实数据驱动，关联项目版本和条目状态。
2. **数据导入/导出**：实现各模块的 Excel 导入导出功能（需求、参数、测试用例）。
3. **PRD 检查功能**：实现 PRD 检查规则库和检查执行逻辑。
4. **原型走查功能**：实现原型截图上传、标注、检查清单。
5. **端到端测试**：验证各模块的创建、编辑、版本管理、关联、Agent 辅助的完整闭环。

## Key Files

| 文件路径 | 变更内容 |
|---------|---------|
| `backend/open_webui/models/pm.py` | 增加 `version_snapshot` 到 relations；完善 entry version 的 diff 存储 |
| `backend/open_webui/routers/pm.py` | 实现版本对比 API、合理性校验 API、Skill 执行 API |
| `src/lib/apis/pm/types.ts` | 完善各模块专属接口，增加版本快照、关联校验结果类型 |
| `src/lib/apis/pm/version.ts` | 增加项目版本对比 API 调用 |
| `src/lib/apis/pm/agent.ts` | 新增：通用 Agent 工具 API 封装 |
| `src/lib/apis/pm/relation.ts` | 增加关联合理性校验 API |
| `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` | 完善模块配置，增加基础信息面板，对接版本和 Agent |
| `src/routes/(app)/pm/[projectId]/versions/+page.svelte` | 增加版本快照详情、版本对比入口 |
| `src/routes/(app)/pm/[projectId]/traceability/+page.svelte` | 增加关联合理性标记、版本上下文展示 |
| `src/lib/components/pm/PMAgentTool.svelte` | 新增：通用 Agent 工具组件 |
| `src/lib/components/pm/PMAgentChatPanel.svelte` | 增强：支持 Skill 路由和动作执行确认 |
| `src/lib/stores/pm/agentChatStore.ts` | 增加 Skill 路由逻辑和动作执行队列 |
| `src/lib/components/pm/PMBaseInfoPanel.svelte` | 新增：条目基础信息展示面板 |
| `src/lib/components/pm/PMVersionTimeline.svelte` | 新增：条目版本流转时间线 |

## Risks & Open Questions

1. **数据模型冲突**：当前统一 `pm_entry` 表与 PRD 期望的独立表结构存在差异。本次计划保持统一表+JSON 的现有架构，通过完善 JSON Schema 来对齐字段，避免大规模数据库迁移。
2. **版本对比性能**：项目级版本对比需要对比大量条目，可能在大型项目中存在性能问题。计划先实现基础 diff，后续考虑增量对比和分页加载。
3. **Agent 准确性**：AI 生成的内容（PRD、测试用例、关联建议）需要用户确认，所有 Agent 动作默认标记为 `pending` 状态，需用户手动应用。
4. **溯源合理性判定规则**：需要产品经理确认各模块间的关联规则（如哪些模块类型之间允许建立 `contains`/`references` 关系）。
5. **OpenWebUI 版本兼容性**：当前代码基于 SvelteKit + OpenWebUI 架构，需确保新增组件与现有设计系统（Tailwind CSS、dark mode）兼容。