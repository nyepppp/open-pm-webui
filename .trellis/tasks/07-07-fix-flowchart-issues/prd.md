# 修复流程图模块问题

## Goal

修复流程图模块的3个问题：点击无响应、加载慢、缺少版本信息。

## Requirements

### 1. 点击无响应
- 在 `/pm/{projectId}/flowchart` 页面，点击流程图列表项能正常打开编辑器
- 修复 `openEntryEditor` 函数的错误处理逻辑

### 2. 流程图加载慢
- 优化流程图编辑器组件，使用更轻量的替代方案或优化现有实现
- 减少不必要的渲染和依赖加载

### 3. 缺少项目版本信息
- 在流程图列表项卡片中显示版本信息（versionNumber）
- 与其他模块（如 architecture）保持一致

## Acceptance Criteria

- [ ] 点击流程图列表项能正常打开编辑器
- [ ] 流程图编辑器加载时间优化
- [ ] 流程图列表项显示版本信息

## Notes

- 相关文件：
  - `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
  - `src/lib/components/pm/PMFlowchartEditor.svelte`
  - `src/lib/components/pm/reactflow/ReactFlowCanvas.svelte`
