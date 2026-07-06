# 功能: 产品路线图与项目排期去重

## Goal

产品路线图和项目排期功能存在重叠，调整产品路线图的功能定位以消除冗余。

## Requirements

- 批注 #7: 产品路线图和项目排期的功能重叠了，调整一下产品路线图的功能
- 选择器: `button[class="flex items-center gap-3 p-4 bg-white dark:bg-gray-850"]`（路线图卡片）
- 页面路径: `/pm/{projectId}`（项目详情页的功能卡片区域）

## Acceptance Criteria

- [ ] 产品路线图功能与项目排期功能不重叠
- [ ] 路线图聚焦于版本规划和里程碑时间线
- [ ] 项目排期聚焦于任务排期和资源分配
