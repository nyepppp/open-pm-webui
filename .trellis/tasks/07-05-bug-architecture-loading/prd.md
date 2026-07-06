# Bug: 产品架构创建后一直加载

## Goal

修复产品架构模块创建后持续处于加载状态、无法显示内容的问题。

## Requirements

- 批注 #15: 产品架构创建后一直在加载
- 页面路径: `/pm/{projectId}/product-architecture`
- 选择器: `div[class="w-full min-h-full h-full px-3"]`

## Acceptance Criteria

- [ ] 产品架构创建后能正常显示内容，不再持续加载
- [ ] 已创建的产品架构列表和详情页正常渲染
