# Implementation Plan: PRD 页面优化

## Task 1: 移除 PRD 章节侧边栏

### 1.1 修改 +page.svelte - 移除章节相关状态
- [ ] 删除 `editingSections` state (line 585)
- [ ] 删除 `editingActiveSection` state (line 586)
- [ ] 删除 `defaultSections` constant (lines 599-606)
- [ ] 删除 `sectionTypeLabels` constant (line 607)
- [ ] 删除 `switchPrdSection()` function (lines 718-731)

### 1.2 修改 +page.svelte - 调整 PRD 打开逻辑
- [ ] 修改 `openEntryEditor` 中的 PRD 处理 (lines 626-634)
  - 不再读取 sections，直接使用 content
  - 向后兼容：如果 data.sections 存在，合并为 content

### 1.3 修改 +page.svelte - 调整 PRD 保存逻辑
- [ ] 修改 `saveEntryContentOnly` 中的 PRD 保存 (lines 681-697)
  - 不再保存 sections 结构
  - 直接保存 content
- [ ] 修改 `saveEntryDoc` 中的 PRD 保存 (lines 774-793)
  - 同上

### 1.4 修改 +page.svelte - 移除章节侧边栏 UI
- [ ] 删除 PRD 章节侧边栏模板 (lines 1816-1839)

### 1.5 修改 +page.svelte - 移除 onChange 中的 sections 更新
- [ ] 删除 onChange 中的 sections 更新逻辑 (lines 2199-2204)

## Task 2: 增强批注功能

### 2.1 验证 PMAnnotationPanel.svelte
- [ ] 检查现有功能是否满足需求
- [ ] 确认点击批注可定位到编辑器位置
- [ ] 确认可以编辑批注内容（通过 AI 修改按钮）
- [ ] 确认可以删除批注

### 2.2 修改 PMRichEditor.svelte - 确保批注面板正常显示
- [ ] 验证 `annotationPanelVisible` 状态控制
- [ ] 验证 `PMAnnotationPanel` 在右侧显示
- [ ] 验证三栏布局（TOC + Editor + Annotation Panel）

### 2.3 修改 PMRichEditor.svelte - 确保批注交互正常
- [ ] 验证选择文本时显示浮动"批注"按钮
- [ ] 验证点击按钮创建批注
- [ ] 验证批注数据通过 `onAnnotationsChange` 回调

## Task 3: 布局调整

### 3.1 确保 PRD 编辑器布局正确
- [ ] 移除章节侧边栏后，编辑器应占满空间
- [ ] TOC 目录在左侧（可选）
- [ ] 批注面板在右侧（可选）

## Validation Steps

1. 打开 PRD 编辑器，确认没有"文档章节"侧边栏
2. 确认 PRD 内容以完整文档形式展示
3. 编辑内容并保存，确认数据格式正确
4. 选择文本，确认显示"批注"按钮
5. 点击批注按钮，确认批注创建成功
6. 打开批注面板，确认批注列表显示
7. 点击批注列表项，确认定位到对应位置
8. 编辑批注内容，确认更新成功
9. 删除批注，确认移除成功
10. 确认 TOC 目录功能正常

## Rollback Points

- 每个 task 完成后 git commit
- 如果出现问题，可以回滚到上一个 commit
