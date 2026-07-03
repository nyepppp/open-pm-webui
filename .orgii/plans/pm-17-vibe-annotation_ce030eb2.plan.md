
# PM 模块全面优化 — 基于 Vibe Annotations 的 17 项修改

## Context

当前 PM 模块前端代码主要集中在两个页面文件：
- `src/routes/(app)/pm/[projectId]/+page.svelte` — 项目工作台首页（状态卡片 + 模块入口 + 最近更新）
- `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` — 所有模块的通用页面（约 1260 行），包含表格视图、表单视图、富文本视图、甘特图、脑图、竞品矩阵等

后端已有 versionStore，但版本字段未在各模块中展示或使用。PRD 定义了完整的版本管理（Versioning 模块）和追溯（Traceability 模块）。

## Approach

按页面/模块分组实施 17 项修改，共 6 个工作单元：

### 1. 项目工作台首页调整（Annotations #1, #2, #3, #4）

**#1 草稿状态卡片挪到最上面**
- 在 `[projectId]/+page.svelte` 中，将状态分布区域（草稿/评审中/已批准/已归档卡片）从模块入口下方移到模块入口上方，作为首页第一屏信息

**#2 规划条目卡片挪到批准卡片下面**
- 将模块分组统计卡片（规划/设计/执行/复盘 条目数）从状态卡片下方移到状态卡片内部，紧接在"已批准"之后显示
- 具体布局：状态卡片 4 列 → 状态卡片 2 行（第一行：草稿+评审中，第二行：已批准+已归档），模块统计紧随其后

**#3 所有文档显示对应版本，所有可选项支持展示对应版本**
- 在模块入口卡片上，从 `currentVersion` store 读取当前版本号，展示在卡片描述旁
- 在"最近更新"列表中，每条记录旁增加版本标签（如 `v1.0`），从 entry 的 `versionId` 或 `data.version` 读取

**#4 新增版本卡片 + 溯源总览卡片**
- 在状态卡片行增加"版本"卡片，展示当前版本号和版本总数
- 增加"溯源"卡片，展示项目内追溯关系总数，点击可跳转 `/pm/{projectId}/traceability`

### 2. FAQ 模块修复（Annotations #5, #6）

**#5 搜索输入框应该可以选中（聚焦/交互）**
- 当前 FAQ 搜索框 `<input class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-850">`，可能被父元素 `overflow` 或 `pointer-events` 阻断交互
- 检查搜索框的 CSS 和父容器，确保 `pointer-events: auto`、无 `overflow: hidden` 截断、`z-index` 正确
- 为输入框添加 `focus:ring-2 focus:ring-blue-500 outline-none` 确保聚焦可见

**#6 关闭按钮放到最左边**
- 当前模块页头部 `{config.name}` 和 `{filteredEntries.length}` 在左侧，`新建`按钮和视图切换在右侧
- FAQ 的搜索框右侧有一个关闭/返回按钮（`p-1.5 rounded-lg dark:hover:bg-gray-800`），将其移到标题左侧
- 实际指 FAQ 表单编辑器头部的返回按钮，将其从右侧移到左侧标题区域

### 3. 参数模块清理（Annotations #7, #8）

**#7 & #8 移除参数表格中的"导出到工作空间"按钮**
- 参数表格每行操作列当前有 4 个按钮：编辑、导出到工作空间、导出为笔记、删除
- 移除 `moduleType === 'parameter'` 条件下渲染的"导出到工作空间"按钮（当前功能只是 `toast.info('开发中')`）
- 同时移除 SVG 图标和 `handleExportToWorkspace` 函数

### 4. PRD 编辑器优化（Annotations #9, #10, #11, #12）

**#9 移除 PRD 左侧章节大纲下方的"📥 导入 Markdown"按钮**
- 当前在 PRD 编辑器的左侧大纲面板底部有 `w-full mt-2 px-2.5 py-2 text-xs rounded-lg` 的导入按钮
- 移除此按钮，仅保留顶部工具栏的"导入"按钮

**#10 修复导入功能：导入后富文本编辑框内没有内容**
- 当前 `onMdFileSelected` 将内容解析为 sections 并追加到 `editingSections`，但 `switchPrdSection` 可能未正确加载内容到富文本编辑器
- 修复：导入完成后，确保 `editingContentHtml` 被正确设置为第一个新 section 的 HTML 内容，并调用 `switchPrdSection` 激活该 section
- 同时确保 `editingContentMd` 被清空，避免 `saveEntryDoc` 时用空的 md 覆盖

**#11 移除 PRD 编辑器顶部的"草稿"状态标签**
- 当前编辑器头部标题旁有一个 `<span class="px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-500">草稿</span>` 静态标签
- 移除此静态标签，状态已通过右侧的下拉选择器展示

**#12 在 PRD 工具栏加入版本更新功能**
- 在 PRD 编辑器头部工具栏（当前有"导入"按钮、状态下拉、保存按钮）增加版本选择/更新功能
- 添加版本下拉选择器，读取 `$currentVersion` store 和版本列表
- 保存时将当前 `versionId` 写入 entry 的 `data` 字段
- 当版本切换时，提示用户是否更新文档内容到对应版本

### 5. 风险模块增强 + 路线图优化（Annotations #13, #14, #15, #16）

**#13 风险表单支持选择功能块**
- 在风险新建表单和编辑表单中增加"关联功能块"选择器
- 类似 testcase 的 `featureOptions`，从 parameter entries 中提取功能名称列表
- 在风险编辑 drawer 中也增加对应的选择器
- 将选中的功能块存入 `data.featureName`

**#14 路线图编辑改为弹窗展示**
- 当前路线图编辑 drawer 使用 `fixed top-0 right-0 w-full max-w-md` 的侧边栏
- 改为居中弹窗（modal），与 PRD/roadmap 编辑 drawer 的 modal 样式统一
- 当前代码已有 `moduleType === 'roadmap'` 的特殊分支使用 `inset-0 flex items-center justify-center`，确认样式一致性

**#15 修复甘特图展示效果**
- 当前甘特图 SVG 在某些日期范围下文字重叠、月份标签截断
- 修复：当 `totalDays` 较大时增加 `dayW` 下限，避免文字溢出
- 月份标签超出范围时截断显示（如 `2026/6` → `6月`）
- SVG 添加 `preserveAspectRatio="xMinYMin meet"` 确保缩放正确
- 确保 `min-width` 足够大，避免压缩导致文字不可读

**#16 路线图新增版本字段**
- 在路线图表格列定义中增加 `{ key: 'versionId', label: '版本', width: 'w-16' }`
- 在新建表单中增加版本下拉选择器（读取版本列表）
- 在编辑 drawer 中增加版本选择
- 表格行中显示版本标签
- 甘特图条形上也显示版本号

### 6. 测试用例增强（Annotation #17）

**#17 测试用例支持关联功能项**
- 当前 testcase 编辑 drawer 已有"关联功能"下拉（`featureName`），使用 `featureOptions`
- 但新建表单中的"关联功能"下拉选项可能为空（因为 `parameterEntries` 在 testcase 模块下未加载）
- 修复 `loadRelatedEntries`：确保 testcase 模块也加载 parameter entries
- 当前代码 `moduleType === 'testcase' || moduleType === 'faq'` 已加载 parameter，确认逻辑正确
- 增强功能：在 testcase 编辑 drawer 中增加"关联功能项"（featureId），可从 parameter entries 的 featureName 列表中选择
- 与 PRD 定义对齐：testcase 应支持 `featureId` 字段关联功能项

## Key Files

| 文件 | 修改内容 |
|------|----------|
| `src/routes/(app)/pm/[projectId]/+page.svelte` | #1 草稿卡片上移、#2 规划卡片位置、#3 版本展示、#4 新增版本+溯源卡片 |
| `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` | #5-17 所有模块页面修改 |
| `src/lib/stores/pm/versionStore.ts` | #3/#4/#12/#16 读取版本数据的 store（无需修改，仅使用） |
| `src/lib/apis/pm/types.ts` | 确认 Version 类型定义（无需修改） |

## Risks & Open Questions

1. **版本数据来源**：当前 entry 数据模型中是否有 `versionId` 字段？如果没有，需要后端配合添加。前端可先用 `data.versionId` 存储。
2. **溯源总览数据**：Annotation #4 提到"溯源看到所有溯源内容"，当前追溯模块是否已有 API 返回关系总数？需要确认 traceability 页面的 API 调用。
3. **甘特图修复范围**：Annotation #15 提到"展示效果有问题"，可能不仅仅是文字重叠，需要实际查看效果后确定修复方案。建议优先确保 SVG viewBox 和 min-width 正确。
4. **PRD 导入 bug (#10)**：需要实际测试导入流程，确认 `switchPrdSection` 是否正确更新了富文本编辑器的绑定值。可能需要调整 `editingContentHtml` 的赋值时机。
5. **功能块数据来源 (#13, #17)**：当前 `featureOptions` 从 parameter entries 的 `featureName` 提取，这依赖用户在参数模块中手动填写 featureName。如果参数模块数据为空，下拉选项也为空。这是数据完整性的问题，非 UI bug。
