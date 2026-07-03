# PM 模块 Vibe Annotation 第二轮修复（14 项）

## Context

基于用户对 PM 工作台的 14 条反馈标注，需要修复图标风格、导入功能、表单字段、甘特图布局、导航交互等问题。涉及文件主要是 `+page.svelte`（模块页）、`+page.svelte`（工作台页）和 `+layout.svelte`（项目布局）。

## Approach

### #1 — 工作台图标改为黑白 SVG（匹配 OpenWebUI 风格）

**问题：** 模块卡片和分组标题使用 emoji 图标，与 OpenWebUI 的 Heroicons outline SVG 风格不统一。

**方案：**
- 将 `moduleGroups` 中的 `icon` 字段从 emoji 改为 SVG path 数据字符串
- 分组 `label` 也去掉 emoji，用纯文本
- 渲染时用内联 `<svg>` 替代 `<span>{mod.icon}</span>`
- 每个模块对应一个 Heroicons outline 图标（24x24 viewBox, stroke-width=2, stroke=currentColor）

图标映射：
- prd → `document-text` | requirement → `clipboard-document-list` | roadmap → `map`
- parameter → `adjustments-horizontal` | product-architecture → `cube` | competitor → `magnifying-glass`
- testcase → `beaker` | risk → `exclamation-triangle` | meeting → `pencil-square`
- acceptance → `check-circle` | faq → `question-mark-circle`

分组标题：规划/设计/执行/复盘（去掉 emoji）

**涉及文件：** `[projectId]/+page.svelte`

### #2 — 工作台新增溯源模块、版本模块、看板增强

**问题：** 工作台只有文件数量统计，缺少溯源模块、版本对比/合并/分支、更丰富的看板视图。

**方案：** 此标注涉及新模块设计，属于产品需求层面，当前无法凭空实现。将标注记录为需求，在当前迭代中做以下可落地改进：
- 看板区域增加按状态（草稿/评审中/已批准/已归档）的分布统计
- 新增"版本"入口卡片（指向版本管理页面，后续迭代实现对比/合并/分支）
- 标注中"溯源模块"作为需求记录，不在本次 UI 修改中新增独立模块

**涉及文件：** `[projectId]/+page.svelte`

### #3 — 验收报告新增对应需求选择

**问题：** acceptance 创建/编辑表单缺少关联需求字段。

**方案：**
- acceptance `formFields` 新增 `{ key: 'requirementId', label: '关联需求', type: 'select' }`
- 渲染 form select 时，如果是 acceptance 模块且 key 为 `requirementId`，从 `requirementEntries` 填充选项
- 需要加载 requirement entries（复用 testcase 已有的 `loadRelatedEntries` 逻辑）

**涉及文件：** `[module]/+page.svelte`

### #4 — FAQ 关联功能改为下拉选择

**问题：** FAQ 的 `relatedFeatures` 字段是文本输入，应该可以选中对应的功能项。

**方案：**
- 将 FAQ `formFields` 中 `relatedFeatures` 的 type 改为 `'select'`
- 渲染 form select 时，如果是 faq 模块且 key 为 `relatedFeatures`，从 parameter entries 填充选项（参数名=功能项）
- 同时也需要加载 parameter entries

**涉及文件：** `[module]/+page.svelte`

### #5 — 参数配置"来源文档"支持 PRD 下拉

**问题：** parameter 的"来源文档"字段是文本输入，应该可以下拉选择 PRD 条目。

**方案：**
- 将参数创建表单的"来源文档"输入框改为 `<select>` 下拉
- 选项从 PRD entries 加载，格式：`PRD 标题 (ID前6位)`
- 保留一个"手动输入"选项（value 为空时使用输入框）
- 需要在 `loadRelatedEntries` 中增加加载 PRD entries

**涉及文件：** `[module]/+page.svelte`

### #6 — PRD 导入 Markdown 后编辑区无内容

**问题：** 点击导入 Markdown 后，富文本编辑区没有内容显示。

**原因：** `onMdFileSelected` 设置了 `editingContentHtml` 和 `editingSections`，但 PRD 编辑器是按 section 渲染的——需要在 section 列表中切换到新 section 才能看到内容。问题可能是 `editingActiveSection` 设置了但 section 内容未正确同步到 `editingContentHtml`，或 RichTextInput 未响应。

**方案：**
- 检查 `switchPrdSection` 函数确保新激活的 section 内容正确传递
- 在导入完成后显式调用 `switchPrdSection(newSections[0].id)` 确保内容同步
- 添加调试：导入后若没有 section，直接将 HTML 写入 editingContentHtml 并确保 RichTextInput 的 value 绑定生效

**涉及文件：** `[module]/+page.svelte`

### #7 — 去掉"+ 添加章节"按钮

**问题：** 用户不需要手动添加章节（通过导入 MD 自动生成章节即可）。

**方案：**
- 删除 PRD 侧边栏中的"+ 添加章节"按钮

**涉及文件：** `[module]/+page.svelte`

### #8 — 导入按钮移至顶部工具栏，支持更多文件类型

**问题：** 导入按钮在侧边栏底部不方便，且只支持 MD 文件。

**方案：**
- 将导入按钮从侧边栏移到 PRD 编辑器顶部工具栏（保存按钮旁边）
- 扩展文件类型支持：`.md,.markdown,.txt,.docx,.pdf`
- `.docx` 和 `.pdf` 暂时标记为"开发中"提示（需要后端解析支持），`.md/.txt` 立即生效
- 导入按钮样式：小图标 + "导入"文字，与保存按钮并排

**涉及文件：** `[module]/+page.svelte`

### #9 — 产品架构应直接显示全版本思维导图，支持版本切换

**问题：** 产品架构模块是 entry 列表视图，用户期望直接看到架构思维导图而非列表。

**方案：**
- 当进入 product-architecture 模块时，若只有一个 entry，直接打开思维导图编辑器（不显示列表）
- 在思维导图编辑器顶部显示当前版本号（从 `$currentVersion` store 读取）
- 列表视图保留但作为辅助：多个架构文档时先列出来让用户选择

**涉及文件：** `[module]/+page.svelte`

### #10 — 去掉需求来源的 PRD 分类

**问题：** 需求来源不需要 PRD 选项。

**方案：**
- 从 `sourceMap` 中删除 `prd` 选项
- 从创建表单的按钮循环中删除 `'prd'`
- 从编辑抽屉的来源按钮循环中删除 `'prd'`
- `newSource` 类型回退为 `'manual' | 'excel' | 'agent'`
- `types.ts` 中 `Requirement.source` 类型也去掉 `'prd'`

**涉及文件：** `[module]/+page.svelte`, `types.ts`

### #11 — 路线图表格新增描述列

**问题：** 路线图表格缺少描述列。

**方案：**
- 在 roadmap `tableColumns` 中新增 `{ key: 'description', label: '描述', width: 'w-32' }`，放在标题列后面
- 表格行渲染中增加对应的 `<td>` 显示 `entry.content`（截断显示）

**涉及文件：** `[module]/+page.svelte`

### #12 — 甘特图布局错误修复

**问题：** 甘特图 SVG 布局有问题，月份标签和任务条位置不对。

**方案：**
- 修复月份头部的 IIFE 渲染：确保月份边界计算正确
- 修复任务条标签位置：名称应显示在条形图左侧区域内，不超出 SVG 边界
- 给 SVG 增加左侧固定列宽（200px）用于显示任务名称
- 调整 `viewBox` 和 `min-width` 计算确保不溢出

**涉及文件：** `[module]/+page.svelte`

### #13 — 路线图创建用弹窗形式，接入日程

**问题：** 路线图创建/编辑当前使用右侧抽屉，用户期望弹窗形式，并接入日程。

**方案：**
- 将路线图的编辑抽屉改为居中弹窗（Modal）样式
- "接入日程"需要后端日程系统支持，当前先添加 `description` 字段到创建/编辑表单
- 弹窗标题改为"创建路线图节点"/"编辑路线图节点"

**涉及文件：** `[module]/+page.svelte`

### #14 — 测试用例新增关联功能

**问题：** testcase 创建表单只有关联需求和关联参数，缺少关联功能。

**方案：**
- 在 testcase 创建表单中新增"关联功能"下拉选择
- 选项从 parameter entries 的 `featureName` 字段去重生成
- 在编辑抽屉中也新增对应字段
- testcase `data` 中增加 `featureName` 字段

**涉及文件：** `[module]/+page.svelte`

## Key Files

| 文件 | 变更内容 |
|------|---------|
| `src/routes/(app)/pm/[projectId]/+page.svelte` | #1 图标改 SVG、#2 看板增强 |
| `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` | #3-6, #8-14 所有模块页修改 |
| `src/lib/apis/pm/types.ts` | #10 去掉 PRD source 类型 |

## Risks & Open Questions

1. **#2 溯源模块和版本对比/合并/分支** — 这些是全新功能模块，需要后端支持，本次只做入口卡片和看板增强
2. **#6 PRD 导入后编辑区无内容** — 需要实际调试确认根因，可能是 section 切换逻辑或 RichTextInput 值绑定问题
3. **#12 甘特图布局** — SVG 内联渲染的月份 IIFE 可能有边界计算问题，需要实际浏览器测试验证
4. **#13 接入日程** — 需要后端日程系统 API，当前仅改 UI 为弹窗形式
5. **#8 导入 docx/pdf** — 前端无法直接解析这些格式，需要后端服务，本次只加按钮和提示
6. **#9 产品架构自动打开** — 若有多个 entry 时直接打开第一个，可能需要确认用户意图