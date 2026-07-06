# Bug: 空状态创建按钮无响应

## Goal

修复 FAQ、Meeting、需求边界、风险模块的空状态下"创建第一个条目"按钮点击无响应的问题。

## Requirements

- 批注 #8: FAQ 页面 — "创建第一个条目" 按钮点击无响应
- 批注 #10: Meeting 页面 — "创建第一个条目" 按钮点击无响应
- 批注 #16: 需求边界页面 — "创建第一个条目" 按钮点击无响应
- 批注 #17: 风险页面 — "创建第一个条目" 按钮点击无响应
- 按钮选择器: `button[class="mt-3 px-4 py-2 text-sm bg-black text-white"]`
- 页面路径: `/pm/{projectId}/{module}` 其中 module 为 faq/meeting/requirement-boundary/risk

## Acceptance Criteria

- [ ] FAQ 空状态"创建第一个条目"按钮点击后进入创建表单
- [ ] Meeting 空状态"创建第一个条目"按钮点击后进入创建表单
- [ ] 需求边界空状态"创建第一个条目"按钮点击后进入创建表单
- [ ] 风险空状态"创建第一个条目"按钮点击后进入创建表单
