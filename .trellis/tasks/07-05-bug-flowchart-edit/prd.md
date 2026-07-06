# Bug: 流程图点击不能编辑

## Goal

修复流程图列表项点击后无法进入编辑状态的问题。

## Requirements

- 批注 #9: 流程图点击后不能编辑相应的流程图
- 选择器: `div[class="px-2.5 py-1 gap-1.5 flex flex-col"]`（列表项）
- 相关组件: `src/lib/components/pm/PMFlowchartEditor.svelte`

## Acceptance Criteria

- [ ] 流程图列表项点击后能进入编辑器
- [ ] 编辑器内可正常编辑节点和连线
