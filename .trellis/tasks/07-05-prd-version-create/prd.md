# PRD 创建新版本功能失效

## Goal

修复 PRD 页面中"创建新版本"按钮功能失效的问题。该按钮应该对需求文档内容做变更版本。

## Context

- **当前实现**: 在 PRD 编辑器中，保存后有 `showSaveVersionDialog = true` 触发版本保存对话框（第797行）
- **版本相关函数**: `saveAsNewVersion()` 函数（第803行）调用 `createEntryVersion` API
- **问题**: Issue 报告"创建新版本"按钮功能失效。需要确认：
  1. 按钮是否存在且可见
  2. 点击后 `saveAsNewVersion()` 是否正常执行
  3. `createEntryVersion` API 是否正常工作
  4. 版本保存后是否正确显示在版本列表中

## Requirements

1. "创建新版本"按钮在 PRD 编辑器中可用
2. 点击后正确调用 `createEntryVersion` API
3. 新版本创建成功后有成功提示
4. 版本历史下拉中能看到新创建的版本

## Acceptance Criteria

- [ ] PRD 编辑器中"创建新版本"按钮可点击
- [ ] 点击后创建新版本成功（toast 提示）
- [ ] 版本历史中显示新版本
