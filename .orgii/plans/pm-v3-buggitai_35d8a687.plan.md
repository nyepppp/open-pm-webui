# PM 工作台 V3 增强计划 — Bug修复·版本Git化·AI打通·参数层级·路线图时间维度

## Context

PM 工作台已有基础框架（10 个模块 CRUD、版本管理、溯源图、富文本编辑器、甘特图），但存在多个 Bug 和功能缺失。用户通过 9 条 Vibe 标注反馈了以下问题，需要逐一修复和增强。

当前技术栈：SvelteKit 5 + SvelteFlow + TipTap + Tailwind + dayjs + mammoth + marked

### 现有 Spec 关系
- `specs/001-pm-workspace-redesign/spec-v2.md` 已覆盖：版本徽章、版本比较/合并/分支、富文本统一、溯源交互增强、甘特图统一
- 本次计划 **新增/修正** 的范围：日期 Bug 修复、版本 Git 化（项目级版本控制入口）、AI 与 OpenWebUI 打通、参数层级选择、PRD 导入改为整文导入、移除章节大纲侧边栏、思维导图数据持久化、路线图时间维度

---

## Approach

### Step 1: 修复 "创建于 Invalid Date" Bug

**问题**：`normalizeTs()` 函数在 `ts` 为 `0`/`undefined`/`null` 时产生 NaN → dayjs 渲染 "Invalid Date"。该函数在 3 个文件中重复出现。

**修复方案**：
1. 创建共享工具函数 `src/lib/utils/pmTimeUtils.ts`，包含 `normalizeTs(ts)` 并增加防御逻辑：
   - `ts` 为 falsy（0/null/undefined/NaN）→ 返回 `Date.now()` 或返回 `null` 让调用方跳过渲染
   - 类型检查：仅处理 number 类型
2. 替换 3 处重复的 `normalizeTs`：
   - `src/routes/(app)/pm/+page.svelte` L124-128
   - `src/routes/(app)/pm/[projectId]/+page.svelte` L138
   - `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` L237
3. 为 "创建于" 添加条件渲染：仅当时间有效时才显示

### Step 2: 版本 Git 化 — 项目级版本控制入口

**问题**：用户希望 "当前版本 v1.1" 卡片点击后能进入项目级版本管理，支持所有模块的版本控制、合并、分支，类似 Git。

**方案**：
1. 将版本卡片改为可点击链接，点击跳转到 `/pm/{projectId}/versions` 页面
2. 新建版本管理页面 `src/routes/(app)/pm/[projectId]/versions/+page.svelte`：
   - **版本列表**：显示所有版本（主线+分支），树形结构
   - **分支操作**：从任意版本创建分支，分支内编辑不影响主线
   - **合并操作**：分支合并回主线，冲突检测与解决界面
   - **版本比较**：选择两个版本，展示所有模块的变更汇总
   - **模块维度**：每个版本下展示各模块的版本快照状态
3. 后端扩展：在 `versionStore` 和 API 中增加分支/合并端点

### Step 3: AI 助手与 OpenWebUI 打通

**问题**：AI 助手卡片显示 "未配置 需配置 AI 模型"，但无配置入口，且未与 OpenWebUI 的聊天能力打通。

**方案**：
1. **AI 状态卡片增强**：
   - 未配置时：添加 "前往配置" 链接，跳转到 OpenWebUI 的模型设置页 (`/workspace/models`)
   - 已配置时：显示模型名称和 "开始对话" 按钮
2. **PMAgentChatPanel 集成**：
   - 复用 OpenWebUI 的 `createNewChat` API 和聊天组件
   - 在 PM 上下文中自动注入项目信息（项目名、当前模块）作为 system prompt
   - 使用 OpenWebUI 的模型选择器逻辑获取可用模型列表
3. **配置流程**：
   - 检测 OpenWebUI 是否已配置模型（复用 `getAgentStatus` → 增强为调用 OpenWebUI 的 `/api/config` 或 models API）
   - 未配置时引导用户去 OpenWebUI 设置页配置 API Key 和模型

### Step 4: 参数层级选择 — 模块→功能→参数

**问题**：参数配置中的 "所属模块" 和 "所属功能" 字段是纯文本输入，用户希望能从已有数据中选择，也可手动输入。

**方案**：
1. 修改 `src/lib/components/pm/moduleFields.ts` 中 `parameterFields`：
   - `moduleId` → 改为 `type: 'cascade-select'`，数据源为当前项目的模块列表
   - `featureId` → 改为 `type: 'cascade-select'`，数据源依赖 `moduleId` 的选择（该模块下的功能条目）
2. 在模块编辑器中实现级联选择组件：
   - 第一级：模块列表（从项目配置获取）
   - 第二级：功能列表（根据选中模块过滤该模块下的条目）
   - 支持手动输入（Combobox 模式：可搜索可输入）
3. 参数排序：按 模块→功能→参数 的层级排列

### Step 5: PRD 导入改为整文导入

**问题**：当前导入按章节（## 标题）拆分为 PRDSection[]，用户希望导入的完整文本直接进入富文本编辑区。

**方案**：
1. 修改 `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` 中的 `onMdFileSelected` 函数：
   - 不再按 `##` / `<h2>` 拆分为章节
   - 将完整转换后的 HTML/Markdown 直接注入到 TipTap 编辑器
   - 保留格式（标题、列表、表格等）
2. 已有 `PMDocumentImporter.svelte` 组件已实现整文导入逻辑，确认 PRD 模块使用此组件而非章节拆分逻辑

### Step 6: 移除 PRD 章节大纲侧边栏

**问题**：用户明确要求 "去掉这个" 章节大纲侧边栏。

**方案**：
1. 在 PRD 编辑器全屏模式下，移除左侧 `PMTableOfContents.svelte` 的渲染
2. 保留 `PMTableOfContents.svelte` 组件文件（其他模块可能仍需要），仅在 PRD 全屏编辑视图中不渲染
3. 目录功能改为编辑器内的浮动目录（可选）：TipTap 编辑器内通过 heading 点击定位

### Step 7: 思维导图数据持久化

**问题**：产品架构的思维导图视图渲染正常，但 `onChange` 回调为空函数，编辑不保存。

**方案**：
1. 在 `[module]/+page.svelte` 中将 `PMMindMap` 的 `onChange` 回调连接到实际的保存逻辑：
   - 将节点变更转换为条目的 CRUD 操作
   - 新增节点 → 创建新条目
   - 删除节点 → 删除条目
   - 移动节点 → 更新条目的 parent/层级关系
2. 添加自动保存提示（debounce 1s 后自动保存）

### Step 8: 路线图时间维度增强

**问题**：路线图甘特图缺少时间维度导航，每行缺少持续天数和描述。

**方案**：
1. **时间维度按钮**：添加 "天/周/月" 切换按钮和 "上一周/下一周" 导航
   - 天视图：按日渲染，每列 1 天
   - 周视图：按周渲染，每列 1 周（当前默认）
   - 月视图：按月渲染，每列 1 月
   - 导航：上一周/下一周（或上/下月，根据当前视图）
2. **每行增强**：
   - 显示实际持续天数（endDate - startDate）
   - 显示描述文字（截断到一行）
   - "今天" 标记线（红色竖线）
3. **甘特图交互增强**：
   - 悬停显示 tooltip（完整描述、日期范围、持续天数）
   - 点击条形图打开编辑抽屉（已有）

---

## Key Files

| 文件路径 | 变更内容 |
|---------|---------|
| `src/lib/utils/pmTimeUtils.ts` | **新建** — 共享时间工具函数 `normalizeTs` |
| `src/routes/(app)/pm/+page.svelte` | 替换本地 `normalizeTs` 为共享函数，修复 "创建于 Invalid Date" |
| `src/routes/(app)/pm/[projectId]/+page.svelte` | 替换 `normalizeTs`；版本卡片改为可点击链接；AI 状态卡片增加配置链接 |
| `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` | 替换 `normalizeTs`；PRD 导入改为整文；移除大纲侧边栏；思维导图 onChange 连接保存；路线图时间维度增强 |
| `src/routes/(app)/pm/[projectId]/versions/+page.svelte` | **新建** — 项目级版本管理页面（分支/合并/比较） |
| `src/lib/components/pm/PMAgentChatPanel.svelte` | 增强 AI 集成，连接 OpenWebUI 聊天 API |
| `src/lib/stores/pm/agentChatStore.ts` | 增强模型状态检测，连接 OpenWebUI 模型 API |
| `src/lib/apis/pm/agentChat.ts` | 增加 OpenWebUI 模型列表查询 |
| `src/lib/components/pm/moduleFields.ts` | 参数字段改为级联选择类型 |
| `src/lib/components/pm/PMCascadeSelect.svelte` | **新建** — 级联选择组件（模块→功能） |
| `src/lib/components/pm/PMMindMap.svelte` | 增强 onChange 数据流，支持持久化 |
| `src/lib/components/pm/PMTableOfContents.svelte` | 保留组件，PRD 编辑器中不渲染 |

---

## Risks & Open Questions

1. **版本 Git 化复杂度**：项目级版本控制涉及跨模块的版本快照、分支/合并冲突检测，后端数据模型需要重新设计。建议分阶段：先实现版本管理入口页 + 版本列表 + 分支创建，合并功能作为 P2。
2. **AI 打通依赖 OpenWebUI API**：需要确认 OpenWebUI 的 `/api/chat/completions` 和 `/api/models` 端点是否可被 PM 模块直接调用，以及认证方式（token 传递）。
3. **级联选择数据源**：功能列表依赖模块选择后的数据加载，需要确认后端是否支持按模块过滤条目的 API，或需要前端全量加载后过滤。
4. **路线图时间维度**：当前甘特图是纯 CSS 实现，增加天/周/月切换和导航需要重构渲染逻辑。考虑是否引入 frappe-gantt 替代自定义实现（v2 spec 中已有此决策）。
5. **PRD 整文导入 vs 章节导入**：改为整文导入后，章节拆分模式是否还需要保留作为可选项？建议默认整文，提供 "按章节拆分" 复选框。
