# PM 工作台 UI 重构：融入 OpenWebUI 设计体系

## Context

用户通过 Vibe Annotations 提出了 5 个核心问题：
1. PM 的独立侧边栏（PMModuleNav）应融合到 OpenWebUI 主侧边栏中，而非双重侧边栏
2. PM 入口应在 OpenWebUI 侧边栏的导航区域中
3. PM 页面 UI 不符合 OpenWebUI 设计体系（Notes/Workspace 风格）
4. TipTap 富文本编辑器无法使用
5. 版本管理 header 不正确（不是多版本管理）

OpenWebUI 的设计体系特征：
- 侧边栏是唯一的导航入口，页面内容区不重复侧边栏
- 内容页面使用 `flex-1 max-h-full overflow-y-auto @container` 布局
- 页面顶部有简洁的导航栏（面包屑 + 操作按钮）
- 列表使用卡片式布局，与 Notes 页面风格一致
- 使用 `$i18n` 国际化、`dayjs` 时间格式化、`toast` 通知

## Approach

### Step 1: 将 PM 模块导航融合到 OpenWebUI 主侧边栏

**核心思路**：移除 PM 独立的 PMModuleNav 侧边栏，改为在 OpenWebUI 主侧边栏中展开 PM 的子模块。

- 在 `Sidebar.svelte` 中，当用户点击 'pm' 侧边栏项时，展开显示 PM 子模块列表（PRD、需求、参数等）
- 参考 OpenWebUI 侧边栏中 'workspace' 的展开逻辑（workspace 点击后跳转到 /workspace，其子页面有 models/knowledge/prompts/tools/skills）
- PM 的子模块按 4 个分类（规划/设计/执行/复盘）组织，每个分类可折叠展开
- 当路由在 `/pm/*` 下时，侧边栏的 'pm' 项高亮，并自动展开子模块

**具体改动**：
- `Sidebar.svelte`：在 'pm' 侧边栏项下方添加子模块展开区域，类似 chat 列表的折叠分组
- `pm/+layout.svelte`：移除 PMModuleNav 组件和独立侧边栏，只保留内容区
- `PMModuleNav.svelte`：重构为侧边栏子组件，供 Sidebar.svelte 内部使用

### Step 2: 重构 PM 页面布局，匹配 OpenWebUI 设计

**核心思路**：PM 页面应像 Notes 页面一样，顶部有简洁导航栏，内容区使用卡片列表。

- 移除 PMProjectHeader（版本管理、项目标题等不属于页面顶部）
- 页面顶部改为：面包屑导航（PM 工作台 > PRD 文档）+ 操作按钮（新建）
- 内容区使用与 Notes 一致的卡片列表样式
- 使用 OpenWebUI 的通用组件：`Tooltip`、`Search`、`Plus`、`Spinner`、`Loader`
- 使用 `$i18n` 国际化、`dayjs` 时间格式化、`toast` 通知

**具体改动**：
- `pm/[module]/+page.svelte`：完全重写页面结构，匹配 Notes 风格
- 移除 `PMProjectHeader` 在 layout 中的使用
- `pm/+layout.svelte`：简化为纯内容容器，无额外 header

### Step 3: 修复 TipTap 富文本编辑器

**核心思路**：当前 PMRichEditor 的 TipTap 初始化可能存在问题。

- 检查 TipTap 编辑器是否正确挂载到 DOM
- 确保 `@tiptap/extension-placeholder` 正确配置
- 添加错误边界和降级处理
- 确保编辑器在 Svelte 5 的 `$effect` 中正确响应 content prop 变化
- 参考 OpenWebUI 自身的富文本编辑器实现（Notes 编辑器）

### Step 4: 简化版本管理

**核心思路**：版本管理不应作为页面 header，而是作为项目设置的一部分。

- 移除 layout 中的 PMProjectHeader 和 PMVersionSelector
- 版本信息改为在项目设置面板中管理（后续实现）
- 当前阶段，页面只显示模块内容，不显示版本 header

## Key Files

| 文件 | 改动 |
|------|------|
| `src/lib/components/layout/Sidebar.svelte` | 添加 PM 子模块展开区域，当 'pm' 激活时显示模块列表 |
| `src/routes/(app)/pm/+layout.svelte` | 移除 PMModuleNav 和 PMProjectHeader，简化为纯内容容器 |
| `src/routes/(app)/pm/[module]/+page.svelte` | 重写为 Notes 风格的卡片列表页面 |
| `src/lib/components/pm/PMModuleNav.svelte` | 重构为侧边栏子组件（供 Sidebar 内嵌使用） |
| `src/lib/components/pm/PMRichEditor.svelte` | 修复 TipTap 初始化和交互问题 |
| `src/lib/components/pm/PMProjectHeader.svelte` | 暂时从 layout 中移除引用 |

## Risks & Open Questions

1. **侧边栏展开逻辑复杂度**：OpenWebUI 侧边栏的 workspace 并没有子模块展开，而是跳转到独立页面。PM 是否也应该跳转到 /pm 后在页面内显示模块列表？用户明确要求"融合到侧边栏"，所以需要实现子模块展开。
2. **TipTap 编辑器问题根因**：需要实际运行 dev server 才能确认编辑器不可用的具体原因（可能是 CSS 问题、初始化时序问题、或 Svelte 5 响应式问题）。
3. **国际化**：当前 PM 组件硬编码中文，后续应使用 `$i18n`，但本次重构先保持中文。
