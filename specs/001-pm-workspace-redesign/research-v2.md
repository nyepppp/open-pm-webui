# Research: PM 工作台增强 v2

**Created**: 2026-06-29

---

## 1. 版本比较·合并·分支

### Decision: 条目级版本控制 + 内嵌对比面板

**Rationale**: 
- 用户已明确版本模型为条目级（per-entry），非项目级快照
- TipTap 基于 ProseMirror，可通过 `prosemirror-collab` + `y-prosemirror` 实现协作文档比较
- 但实际场景中更简单的方式：存储每次保存的内容快照（content JSON），对比两个快照的差异
- frappe-gantt 和 chart.js 已安装，无需额外引入

**Alternatives considered**:
- Git-like diff（引入 isomorphic-git）→ 过重，Svelte 前端不需要完整 git
- ProseMirror collab（y-prosemirror）→ 适合实时协作，但版本比较需要的是快照对比
- 简单 JSON diff → 最实用，对比两个 TipTap JSON 文档的节点差异

**Implementation approach**:
- 每次 entry 保存时，后端存储一个 content 快照（EntryVersion 表）
- 前端对比：取两个版本的 TipTap JSON，递归比较节点差异，高亮显示
- 分支：在 EntryVersion 上加 branchName 字段，默认 "main"
- 合并：取分支最新版本和主线最新版本，三路对比，标记冲突

---

## 2. 思维导图库选型

### Decision: mind-elixir

**Rationale**:
- MIT 协议，可直接集成
- 纯 vanilla JS，无框架依赖，可包装为 Svelte 组件
- 支持拖拽、折叠、主题、导出、右键菜单
- npm 周下载量较高，社区活跃
- API 简洁：`new MindElixir({ el, data })` 即可初始化
- 支持自定义节点渲染，可扩展为产品架构图

**Alternatives considered**:
- jsMind → 较老，API 不够现代，但稳定
- simple-mind-map → 功能丰富但包较大（canvas-based），性能风险
- markmap → 基于 markdown，适合只读展示，不适合交互编辑
- @xyflow/svelte → 已安装，但它是流程图库，做思维导图需要大量自定义节点逻辑

**Integration plan**:
- 安装 mind-elixir
- 创建 PMMindMapEditor.svelte 包装组件
- 数据格式：mind-elixir 自有格式 ↔ PM 后端数据模型互转
- 替换当前 PMMindMap.svelte 中的 xyflow 实现

---

## 3. 甘特图实现

### Decision: frappe-gantt（已安装）

**Rationale**:
- package.json 已包含 `frappe-gantt: ^1.2.2`
- 轻量级，SVG-based，支持拖拽、缩放、依赖关系
- API 简洁：`new Gantt(svg, tasks, options)`
- MIT 协议

**Alternatives considered**:
- dhtmlx-gantt → 功能更强但商业协议
- 自定义 SVG → 开发量过大
- chart.js 横向条形图 → 不是真正的甘特图

**Integration plan**:
- 创建 PMGanttChart.svelte 共享组件
- 统一任务数据格式：`{ id, name, start, end, progress, dependencies }`
- 路线图和排期模块共用
- 支持视图模式切换：列表 / 甘特图

---

## 4. 日程集成

### Decision: 复用 OpenWebUI 日历系统

**Rationale**:
- OpenWebUI 已有完整的日历系统：
  - 后端：`backend/open_webui/routers/calendar.py`、`models/calendar.py`
  - 前端：`src/lib/apis/calendar/index.ts`、`CalendarView.svelte`、`CalendarEventModal.svelte`、`CalendarSidebar.svelte`
  - 路由：`src/routes/(app)/calendar/+page.svelte`
- CalendarEventModel 支持 data/meta 字段，可存储 PM 关联信息
- 无需新建日历组件，直接调用现有 API

**Integration plan**:
- 在 PM 条目保存时，调用 calendar API 创建/更新事件
- 事件的 data 字段存储：`{ pmEntityType: 'roadmap', pmEntityId: 'xxx', pmProjectId: 'xxx' }`
- 日历事件点击时，检测 data 中的 PM 信息，跳转到 PM 模块
- PM 工作台侧边栏增加日程概览组件（调用 calendar API 获取本周事件）

---

## 5. 文档导入

### Decision: mammoth (.docx) + marked (.md) → TipTap

**Rationale**:
- mammoth 已安装（`mammoth: ^1.12.0`），可将 .docx 转为 HTML
- marked 已安装（`marked: ^9.1.0`），可将 .md 转为 HTML
- TipTap 可直接注入 HTML 内容
- 导入整篇文本，而非按章节拆分

**Integration plan**:
- 创建 PMDocumentImporter.svelte 组件
- .docx：mammoth → HTML → TipTap editor.commands.setContent(html)
- .md：marked → HTML → TipTap editor.commands.setContent(html)
- .txt：直接作为纯文本插入
- 替换当前的"导入章节"逻辑

---

## 6. 自动目录

### Decision: TipTap heading 提取 + PMTableOfContents.svelte

**Rationale**:
- TipTap 文档是 ProseMirror JSON 结构，可遍历提取 heading 节点
- 监听 editor 的 update 事件，实时提取 headings
- 无需额外依赖

**Integration plan**:
- 创建 PMTableOfContents.svelte 组件
- 接收 TipTap editor 实例作为 prop
- 监听 update 事件，提取所有 heading 节点（level 1-6）
- 渲染为可折叠目录树，点击跳转到对应位置
- 集成到 PMRichEditor.svelte 的侧边栏区域

---

## 7. 溯源交互增强

### Decision: @xyflow/svelte + 自定义交互层

**Rationale**:
- @xyflow/svelte 已安装，当前 PMTraceabilityGraph.svelte 使用它
- xyflow 原生支持边（edge）的拖拽创建（通过 onConnect 回调）
- 需要添加：节点点击详情面板、连线创建关联、右键菜单、双击跳转

**Integration plan**:
- 启用 xyflow 的 connection line 功能（用户从节点 port 拖拽创建边）
- onConnect 回调 → 弹出关系类型选择器 → 调用 relation API 创建关联
- 单击节点 → 右侧 PMTraceDetailPanel.svelte（条目详情 + 编辑）
- 右键边 → 上下文菜单（修改关系类型、删除、影响分析）
- 双击节点 → navigate 到模块编辑页

---

## 8. 富文本统一

### Decision: 统一 PMRichEditor 配置

**Rationale**:
- 当前 PMRichEditor.svelte 已封装 TipTap，但各模块可能使用不同的扩展配置
- TipTap 扩展已完整安装：starter-kit, image, link, table, code-block-lowlight, highlight, list, mention, placeholder, typography, youtube, bubble-menu, floating-menu, drag-handle, file-handler

**Integration plan**:
- 定义统一的 TipTap 扩展配置集（PM_TIPTAP_EXTENSIONS）
- 所有富文本模块使用同一配置初始化
- 增加目录生成功能（PMTableOfContents.svelte）
- 增加文档导入功能（PMDocumentImporter.svelte）

---

## 9. 可复用的 OpenWebUI 组件清单

| 组件 | 路径 | 用途 |
|------|------|------|
| CalendarView | src/lib/components/calendar/CalendarView.svelte | 日程集成 |
| CalendarEventModal | src/lib/components/calendar/CalendarEventModal.svelte | PM 事件编辑 |
| CalendarSidebar | src/lib/components/calendar/CalendarSidebar.svelte | 日程概览 |
| Calendar API | src/lib/apis/calendar/index.ts | 日历 CRUD |
| File upload | 搜索现有文件上传组件 | 文档导入 |
| Document viewer | 搜索现有文档预览组件 | 文档预览 |

---

## 10. 已安装的关键 npm 包

| 包名 | 版本 | 用途 |
|------|------|------|
| @tiptap/core | ^3.0.7 | 富文本编辑器核心 |
| @tiptap/starter-kit | ^3.0.7 | 基础扩展集 |
| @tiptap/extension-image | ^3.0.7 | 图片插入 |
| @tiptap/extension-table | ^3.0.7 | 表格 |
| @tiptap/extension-highlight | ^3.3.0 | 高亮 |
| @tiptap/extension-link | ^3.0.7 | 链接 |
| @tiptap/extension-code-block-lowlight | ^3.0.7 | 代码块 |
| @tiptap/extension-list | ^3.0.7 | 列表 |
| @tiptap/extension-mention | ^3.0.9 | @提及 |
| @tiptap/extension-drag-handle | ^3.4.5 | 拖拽句柄 |
| @tiptap/extension-file-handler | ^3.0.7 | 文件处理 |
| @xyflow/svelte | ^0.1.19 | 流程图/溯源图 |
| frappe-gantt | ^1.2.2 | 甘特图 |
| chart.js | ^4.5.0 | 图表 |
| mermaid | ^11.10.1 | 流程图渲染 |
| mammoth | ^1.12.0 | .docx 解析 |
| marked | ^9.1.0 | Markdown 解析 |
| dayjs | ^1.11.10 | 日期处理 |
| xlsx | ^0.18.5 | Excel 导入导出 |
| yjs | ^13.6.27 | 协作（未来） |
| zod | ^4.4.3 | 表单验证 |
