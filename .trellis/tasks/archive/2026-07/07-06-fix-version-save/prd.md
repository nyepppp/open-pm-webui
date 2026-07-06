# 修复版本保存功能

## Goal

修复 PRD 编辑器中的版本保存功能，确保：
1. **保存按钮**保存文件版本（entry-level）而非项目版本（project-level）
2. **创建新版本**功能正常工作，不再报错
3. **版本选择器**正确显示文件版本

## Background

当前 PRD 编辑器（`[module]/+page.svelte`）中的保存逻辑存在以下问题：

- **保存按钮** (`saveEntryDoc`)：调用 `updateEntry` 直接更新条目内容，但保存后弹出的 `PMSaveVersionDialog` 让用户选择"仅保存内容"或"创建新版本"。当前"仅保存内容"只是关闭对话框，没有实际保存。
- **创建新版本** (`saveAsNewVersion`)：调用 `createEntryVersion` API，但可能因参数错误或后端接口不匹配而报错。
- **版本选择器**：显示的是项目版本列表（`$versionList`），但用户标注确认这是正确的（文件版本）。

相关代码位置：
- `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` 第 782-852 行
- `src/lib/components/pm/PMSaveVersionDialog.svelte`
- `src/lib/apis/pm/version.ts`

## Requirements

### R1: 修复"保存"按钮行为
- 点击"保存"按钮时，应直接保存当前文件内容（调用 `saveEntryContentOnly` 或 `saveEntryDoc`）
- 保存成功后弹出 `PMSaveVersionDialog`，提供两个选项：
  - **仅保存内容**：关闭对话框，内容已保存（当前版本更新）
  - **创建新版本**：调用 `createEntryVersion` 创建条目新版本

### R2: 修复"创建新版本"功能
- `saveAsNewVersion` 函数需要正确调用 `createEntryVersion` API
- 检查 API 参数是否正确传递（`projectId`, `entryId`, `changeSummary`, `branchName`, `projectVersionId`）
- 处理可能的错误情况（404/405 等）

### R3: 版本选择器保持现状
- 版本选择器显示文件版本是正确的，无需修改
- 确保版本选择器在保存后能正确刷新

## Acceptance Criteria

- [ ] 点击"保存"按钮后，文件内容被正确保存
- [ ] 保存成功后弹出版本管理对话框
- [ ] "仅保存内容"选项关闭对话框，内容已保存
- [ ] "创建新版本"选项成功创建新版本，不报错
- [ ] 版本选择器正确显示文件版本

## Notes

- 当前自动保存（`saveEntryContentOnly`）每 30 秒触发一次，覆盖当前版本内容
- 手动保存（`saveEntryDoc`）后弹出版本管理对话框，让用户选择是否创建新版本
- 需要检查后端 API `/projects/{projectId}/entries/{entryId}/versions` 是否正常工作
