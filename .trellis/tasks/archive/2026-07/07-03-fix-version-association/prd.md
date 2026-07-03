# 修复页面版本关联缺失及路线图多余列

## Goal

修复3个页面问题：(1) 会议纪要列表未显示版本关联；(2) PRD文档列表未显示版本关联；(3) 路线图表格版本列显示了原始UUID而非版本号。

## Background

文件 `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` 是所有模块的统一页面，模块配置通过 `moduleConfig` 字典驱动。

**问题1 & 2：会议纪要和PRD文档列表未显示版本关联**

- `meeting` 和 `prd` 的 `editorType` 为 `'rich'`，走卡片列表视图
- 卡片视图中已有版本 badge 渲染逻辑（读取 `entry.data.versionId`，查 `$versionList` 显示版本号），但显示为 `-`（灰色）
- 创建 entry 时（`handleCreate`，line 247-254）会自动关联 `currentVersion`，将 `versionId` 写入 `data.versionId` 和顶层 `data.versionId`
- 旧 entry 可能没有关联版本号

**问题3：路线图表格版本列显示UUID**

- Roadmap 的 `tableColumns` 中有 `currentVersionNumber` 列（width `w-20`）
- Line 1307-1316：`currentVersionNumber` 列渲染时，`entry.currentVersionNumber` 为空显示 `-`，不为空时直接显示原始值
- 当后端返回 UUID 格式的值时，直接显示原始 UUID 而非人类可读版本号

## Requirements

### R1: 会议纪要和PRD卡片列表显示版本信息
- 卡片列表中已有版本 badge，需确保版本关联数据正确时能正确显示版本号
- 当 entry 没有关联版本时，显示 `-` 或"未关联"

### R2: 会议纪要和PRD条目支持手动关联/修改版本
- 编辑界面中，允许用户为 meeting/prd 条目设置版本关联
- 复用已有的版本选择器（`$versionList` 下拉框），与 roadmap 编辑 drawer 中的版本选择器一致

### R3: 路线图表格版本列显示版本号而非UUID
- 当 `currentVersionNumber` 是 UUID 格式时，应查 `$versionList` 显示人类可读的版本号
- 或者改为使用 `versionId` + `$versionList` 查找（与 meeting/prd 卡片逻辑一致）
- 如果 entry 既没有 `currentVersionNumber` 也没有 `data.versionId`，显示 `-`

## Acceptance Criteria

- [ ] 会议纪要卡片列表中，已关联版本的条目显示正确版本号（蓝色 badge）
- [ ] PRD文档卡片列表中，已关联版本的条目显示正确版本号（蓝色 badge）
- [ ] 会议纪要/PRD条目可通过编辑界面关联或修改版本
- [ ] 路线图表格的版本列不再显示原始 UUID，而是显示可读版本号
- [ ] 未关联版本的条目统一显示 `-`（灰色文字）

## Notes

- 所有修改集中在 `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` 一个文件
- 版本数据源 `$versionList` 已在页面中可用
- 轻量级任务，PRD-only
