# 修复流程图模块三大问题

## Goal

修复流程图模块的三个关键问题，提升用户体验和性能。

## Requirements

### R1: 修复流程图点击打开编辑器
- 流程图列表项点击时应正确调用 `openEntryEditor` 打开编辑器
- 当前 flowchart 模块的列表项点击事件可能未正确绑定或执行

### R2: 用轻量级 SVG 组件替换 ReactFlow
- 将 `ReactFlowCanvas.svelte` 中的 `@xyflow/svelte` 依赖替换为自定义 SVG 实现
- 保持现有功能：节点渲染、边线连接、点击交互、只读模式
- 减少打包体积和加载时间

### R3: 流程图列表显示版本信息
- 在流程图列表项中显示版本信息（类似 architecture 模块）
- 显示格式：版本号标签（蓝色圆角标签）
- 版本号来源：`entry.currentVersionNumber` 或 `entry.versionId`

## Acceptance Criteria

- [ ] 点击流程图列表项能正确打开编辑器
- [ ] ReactFlowCanvas 使用 SVG 实现，不依赖 `@xyflow/svelte`
- [ ] SVG 实现支持：节点显示、边线连接、节点点击、画布点击、只读模式
- [ ] 流程图列表项显示版本信息标签
- [ ] 所有变更不影响其他模块功能

## Notes

- 参考 architecture 模块的版本显示实现（`+page.svelte` 中 `cardVersionId` 相关逻辑）
- 当前 ReactFlowCanvas 使用 `@xyflow/svelte` 的 `SvelteFlow`、`Background`、`Controls`、`MiniMap` 组件
- 文件位置：
  - `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
  - `src/lib/components/pm/reactflow/ReactFlowCanvas.svelte`
