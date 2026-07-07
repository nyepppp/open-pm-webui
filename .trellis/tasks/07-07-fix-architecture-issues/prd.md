# 修复产品架构页面问题

## Goal

修复产品架构页面的5个关键问题，提升用户体验和页面性能。

## Requirements

### 1. 工作台分页问题 (Dashboard Pagination)
- **问题**: 工作台"最近更新"列表显示超过20条数据但没有分页
- **位置**: `src/routes/(app)/pm/[projectId]/+page.svelte`
- **现状**: 代码中已有分页逻辑，但 `recentItems` 被硬编码为只取前20条 (`recentItems = sorted.slice(0, 20)`)
- **修复**: 
  - 移除 `recentItems` 的20条限制，让分页组件正常工作
  - 确保分页控件在数据超过20条时正确显示

### 2. 架构页面性能问题 (Page Performance)
- **问题**: 产品架构页面整体卡顿
- **位置**: `src/routes/(app)/pm/[projectId]/architecture/+page.svelte`
- **分析**: 
  - Excalidraw 在 `viewModeEnabled=true` 模式下仍可能消耗大量资源
  - `treeToExcalidraw` 每次数据变化都重新生成所有元素
  - 页面加载时同时加载了3个tab的内容（即使只显示一个）
- **修复**:
  - 优化 ExcalidrawCanvas 组件，使用 `key` 控制重新渲染
  - 对 `treeToExcalidraw` 结果进行缓存，避免重复计算
  - 使用 `{#key}` 或条件渲染优化tab切换

### 3. 按钮不可点击问题 (Button Clickability)
- **问题**: 架构页面所有按钮都点击不了
- **位置**: `src/routes/(app)/pm/[projectId]/architecture/+page.svelte`
- **分析**: 
  - 检查是否有 `pointer-events-none` 或其他CSS覆盖
  - 检查 Excalidraw canvas 是否覆盖了按钮区域
  - 检查 z-index 问题
- **修复**: 
  - 确保按钮层级正确
  - 检查并修复可能的CSS覆盖问题

### 4. 思维导图结构问题 (Mindmap Structure)
- **问题**: 思维导图显示为乱序/无结构
- **位置**: `src/lib/utils/excalidrawDataConverter.ts` 中的 `treeToExcalidraw`
- **分析**: 
  - `treeToExcalidraw` 函数生成的节点位置计算可能有问题
  - 模块和功能的坐标计算可能导致重叠
  - 箭头连接点可能不正确
- **修复**:
  - 重新设计布局算法，使用树形布局
  - 确保模块水平均匀分布
  - 确保功能垂直排列不重叠
  - 添加适当的间距和对齐

### 5. 功能列表布局问题 (Feature List Layout)
- **问题**: 功能列表布局不正确，应该改为表格结构
- **位置**: `src/lib/components/pm/ModuleFeatureManager.svelte`
- **分析**: 
  - 当前使用卡片式布局，用户反馈应该使用表格
  - 操作按钮（编辑描述、删除）应该与其他模块表单保持一致
- **修复**:
  - 将模块/功能列表改为表格布局
  - 表头包含：模块名称、功能数量、描述、操作
  - 功能列表作为子表格展开
  - 操作按钮使用统一的样式

## Acceptance Criteria

- [ ] 工作台"最近更新"列表正确分页，超过20条时显示分页控件
- [ ] 产品架构页面加载和切换tab时无明显卡顿
- [ ] 所有按钮（版本选择、AI助手、tab切换等）可正常点击
- [ ] 思维导图按树形结构正确显示，模块和功能不重叠
- [ ] 功能列表改为表格布局，与其他模块表单风格一致

## Notes

- 所有修改应遵循现有代码风格和Tailwind CSS使用规范
- 确保深色模式兼容性
- 修改后需要测试响应式布局
