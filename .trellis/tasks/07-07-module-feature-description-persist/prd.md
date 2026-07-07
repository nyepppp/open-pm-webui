# 模块/功能描述持久化

## Goal

将模块/功能的描述数据持久化到后端，而不是仅存储在前端状态中。

## Requirements

### 数据模型
- 模块描述：存储在 `product-architecture` 条目的 `data.description` 字段
- 功能描述：存储在 `product-architecture` 条目的 `data.features` 数组中

### 功能需求
1. **加载描述**：页面加载时，从后端获取模块/功能的描述数据
2. **保存描述**：编辑描述后，保存到后端
3. **数据同步**：描述数据与架构数据同步

### API设计
- `GET /projects/{projectId}/modules/product-architecture` - 获取架构条目
- `PUT /projects/{projectId}/modules/product-architecture/{id}` - 更新架构条目

## Acceptance Criteria

- [ ] 页面加载时自动加载模块/功能描述
- [ ] 编辑描述后可以保存到后端
- [ ] 描述数据与架构数据同步
- [ ] 添加/删除模块/功能时，描述数据同步更新

## Notes

- 使用现有的 `architectureService` API
- 描述数据存储在 `entry.data.description` 和 `entry.data.features` 中
