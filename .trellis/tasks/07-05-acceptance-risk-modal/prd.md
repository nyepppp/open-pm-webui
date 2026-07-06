# 验收报告/风险分析新增弹窗失效

## Goal

修复验收报告 (acceptance) 和风险分析 (risk) 页面中"新建"按钮点击无效、没有新增内容弹窗的问题。

## Context

- **当前实现**: 在 `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` 中：
  - 所有模块共用同一个"新建"按钮（第1021行），点击后设置 `showNewForm = true`
  - `showNewForm` 为 true 时显示内联表单（第1070行起）
  - acceptance 和 risk 都是 `editorType: 'form'` 类型，有各自的内联表单模板
- **代码分析**: 点击"新建"按钮后 `showNewForm` 应该设为 true，内联表单应该显示。acceptance 表单在第1110-1123行，risk 表单在第1089-1109行。表单代码存在且完整。
- **可能原因**:
  1. 表单区域可能被其他条件渲染覆盖
  2. `handleCreate` 中 form 类型的创建逻辑可能有 bug
  3. UI 层面的 z-index 或溢出问题

## Requirements

1. 点击"新建"按钮后，acceptance 和 risk 页面正确显示内联创建表单
2. 填写表单后点"创建"按钮能成功创建条目
3. 创建后列表刷新显示新条目

## Acceptance Criteria

- [ ] acceptance 页面点击"新建"显示内联表单
- [ ] risk 页面点击"新建"显示内联表单
- [ ] 填写表单并创建后条目出现在列表中
- [ ] 取消按钮正常关闭表单
