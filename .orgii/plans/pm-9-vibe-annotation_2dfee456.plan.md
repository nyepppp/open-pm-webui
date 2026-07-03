# PM 模块增强计划 — 9 项 Vibe Annotation 修复

## Context

当前 PM 模块系统基于 `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` 单文件实现，所有模块（competitor、requirement、prd、roadmap、testcase、product-architecture 等）共享同一页面，通过 `moduleConfig` 配置区分编辑器类型（rich/table/form/mindmap）。

**现有问题汇总（9 个标注）：**
1. **竞品分析编辑器太简陋** — 只有 5 个纯文本字段，缺少维度评分矩阵、对比表格等结构化编辑
2. **需求管理表格缺少编辑操作** — 操作列只有导出/删除，无内联编辑
3. **需求来源缺少 PRD 选项** — sourceMap 只有 manual/excel/agent
4. **工作台缺少看板和最近活动** — 只有模块入口卡片，无看板视图、无最近新增内容流
5. **PRD 不支持导入 MD 文档且不解析 MD** — 只能手动输入，无法导入 .md 文件
6. **返回按钮交互不对** — 只有一个返回项目列表的箭头，缺少"返回首页"和"返回上一步"以及面包屑
7. **产品架构思维导图未实现** — 显示"开发中"占位，实际已有 `@xyflow/svelte` 依赖和 `PMMindMap.svelte` 组件
8. **路线图缺少甘特图视图** — 只有表格，无法切换甘特图视图
9. **测试用例创建表单中需求和功能模块应为下拉选择** — 当前是手动输入 ID

## Approach

### 1. 竞品分析 — 结构化维度评分矩阵编辑器（Annotation #1）

**现状：** competitor 使用 `editorType: 'form'`，5 个纯文本字段（竞品URL、分析维度、我方产品、竞品、分析结论）

**改造：**
- 将 competitor 的 `editorType` 改为 `'competitor'`（新增专用类型）
- 编辑器内实现维度评分矩阵：每行一个维度（名称 + 我方评分 0-100 + 竞品评分 0-100 + 备注），可动态增删行
- 顶部保留竞品名称、URL、描述字段
- 底部增加分析结论富文本区域
- 列表视图展示维度对比雷达图摘要（简化为评分对比条）

**涉及文件：**
- `[module]/+page.svelte` — 新增 competitor 专用编辑器模板和 `moduleConfig` 修改
- `types.ts` — Competitor/CompetitorDimension 类型已有，确认 data 存储格式

### 2. 需求管理 — 表格内联编辑（Annotation #2）

**现状：** requirement 使用 `editorType: 'table'`，操作列只有导出笔记和删除

**改造：**
- 在表格操作列增加"编辑"按钮（铅笔图标）
- 点击编辑按钮弹出侧边编辑面板（Drawer），包含：标题、描述、来源、分类、优先级、状态
- 编辑面板保存后刷新列表
- 同时支持双击行进入编辑

**涉及文件：**
- `[module]/+page.svelte` — 新增编辑 Drawer 组件和编辑逻辑

### 3. 需求来源新增 PRD 选项（Annotation #3）

**现状：** `sourceMap` 只有 manual/excel/agent 三个选项

**改造：**
- `sourceMap` 新增 `prd: { l: 'PRD', c: 'bg-blue-100 text-blue-600 ...' }`
- `newSource` 类型扩展为 `'manual' | 'excel' | 'agent' | 'prd'`
- 后端 Requirement 类型 `source` 字段同步扩展

**涉及文件：**
- `[module]/+page.svelte` — sourceMap 和 newSource 类型
- `types.ts` — Requirement.source 类型

### 4. 工作台 — 看板视图 + 最近活动流（Annotation #4）

**现状：** `[projectId]/+page.svelte` 只有模块入口卡片网格

**改造：**
- 页面顶部保留模块入口卡片（现有布局）
- 新增看板区域：按模块分类的统计卡片（各模块条目数、最近更新时间）
- 页面底部新增"最近活动"时间线：
  - 每条记录显示：标题、所属模块（带图标）、时间、操作人
  - 点击标题导航到对应模块条目
  - 调用后端 API 获取最近更新的 entries（按 updatedAt 排序，取前 20 条）
- 需要新增后端 API：`GET /pm/projects/{id}/recent-activities`

**涉及文件：**
- `[projectId]/+page.svelte` — 新增看板统计和活动流 UI
- `backend/open_webui/routers/pm.py` — 新增 recent-activities 端点
- `$lib/apis/pm/index.ts` — 新增 API 调用函数

### 5. PRD 导入 MD 文档 + MD 解析（Annotation #5）

**现状：** PRD 编辑器只支持手动在 RichTextInput 中输入

**改造：**
- PRD 编辑器顶部工具栏增加"导入"按钮
- 点击后弹出文件选择器（accept=".md,.markdown,.txt"）
- 读取文件内容后使用 `marked` 库（已有依赖）解析 MD 为 HTML
- 将解析结果填入当前 PRD section 的 content
- 同时支持将整个 MD 文件按 `#` 标题拆分为多个 PRD section（自动识别章节结构）

**涉及文件：**
- `[module]/+page.svelte` — PRD 编辑器区域增加导入按钮和 MD 解析逻辑

### 6. 导航 — 返回首页 + 返回上一步 + 面包屑（Annotation #6）

**现状：** `[projectId]/+layout.svelte` 顶部只有一个左箭头返回 `/pm`（项目列表）

**改造：**
- 将单个返回箭头替换为面包屑导航：`PM 首页 > 项目名 > 模块名`
- 面包屑左侧保留"返回首页"图标按钮（goto `/pm`）
- 面包屑右侧保留"返回上一步"图标按钮（`history.back()` 或根据当前路由计算）
- 面包屑各段可点击跳转

**涉及文件：**
- `[projectId]/+layout.svelte` — 替换返回按钮为面包屑组件
- 新建 `PMBreadcrumb.svelte` 组件（可选，或内联实现）

### 7. 产品架构 — 启用思维导图（Annotation #7）

**现状：** product-architecture 编辑器显示"💡 思维导图模式开发中"占位文字，但 `PMMindMap.svelte` 组件和 `@xyflow/svelte` 依赖已存在

**改造：**
- 将 product-architecture 的编辑器从占位文字替换为 `PMMindMap` 组件
- 传入当前 entry 的 mindmap nodes 数据
- 保存时将 mindmap nodes 序列化到 entry.data
- 需要确认 PMMindMap 组件的 props 接口与当前数据格式匹配

**涉及文件：**
- `[module]/+page.svelte` — mindmap 编辑器区域替换占位为 PMMindMap 组件
- `PMMindMap.svelte` — 可能需要微调 props 适配

### 8. 路线图 — 甘特图视图切换（Annotation #8）

**现状：** roadmap 只有表格视图，显示节点名称/类型/状态/开始结束/依赖

**改造：**
- 路线图顶部增加视图切换按钮：表格视图 / 甘特图视图
- 甘特图视图使用开源组件实现（推荐 `frappe-gantt` 或自建简易甘特图）
- 甘特图数据从 roadmap entries 的 startDate/endDate/dependencies 映射
- 新增 npm 依赖：`frappe-gantt`（轻量，~5KB gzip）

**涉及文件：**
- `[module]/+page.svelte` — 新增甘特图视图切换和渲染
- `package.json` — 新增 frappe-gantt 依赖

### 9. 测试用例 — 需求和功能模块下拉选择（Annotation #9）

**现状：** testcase 创建表单中"关联需求ID"和"关联参数ID"是手动输入文本框

**改造：**
- 将"关联需求ID"改为下拉选择，选项从当前项目的 requirement entries 加载
- 将"关联参数ID"改为下拉选择，选项从当前项目的 parameter entries 加载
- 下拉选项显示格式：`[优先级] 标题 (ID前6位)`
- 编辑器中同样改为下拉

**涉及文件：**
- `[module]/+page.svelte` — testcase 创建/编辑表单中替换 input 为 select，加载关联数据

## Key Files

| 文件 | 变更内容 |
|------|---------|
| `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` | 所有 9 项标注的核心修改文件：competitor 编辑器、requirement 编辑 Drawer、sourceMap 扩展、PRD 导入、mindmap 启用、甘特图视图、testcase 下拉 |
| `src/routes/(app)/pm/[projectId]/+page.svelte` | 工作台看板和最近活动流 |
| `src/routes/(app)/pm/[projectId]/+layout.svelte` | 面包屑导航替换返回按钮 |
| `src/lib/apis/pm/types.ts` | Requirement.source 类型扩展 |
| `src/lib/components/pm/PMMindMap.svelte` | 可能微调 props 适配 |
| `backend/open_webui/routers/pm.py` | 新增 recent-activities API |
| `src/lib/apis/pm/index.ts` | 新增 recent-activities 前端调用 |
| `package.json` | 新增 frappe-gantt 依赖 |

## Risks & Open Questions

1. **甘特图组件选型** — `frappe-gantt` 是否支持 Svelte 集成？可能需要用 `onMount` + DOM 操作初始化。备选方案：自建简易 SVG 甘特图（无额外依赖）。
2. **PMMindMap 组件就绪度** — 组件已存在但可能未完整实现交互（拖拽、编辑节点），需要验证功能完整性。
3. **工作台最近活动 API** — 后端需要新增聚合查询端点，需确认数据库 schema 是否支持跨模块查询。
4. **PRD MD 导入的章节拆分** — 按 `#` 标题拆分是常见做法，但 MD 文件结构多样，可能需要容错处理。
5. **单文件膨胀** — `[module]/+page.svelte` 已有 739 行，9 项改动会进一步膨胀。建议在实施时将各模块编辑器抽取为独立组件（如 `PMCompetitorEditor.svelte`、`PMGanttView.svelte` 等），但本计划先聚焦功能实现。
