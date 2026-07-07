# 架构模块功能增强 - 3 Tab页

## Goal

重构架构页面，将当前单一的参数表格页面扩展为3个Tab页，分别展示思维导图、模块/功能描述管理和参数表格。

## Requirements

### Tab 1: 思维导图（第一页）
- 使用现有 `PMMindMap` 组件展示架构思维导图
- **不支持编辑**，仅展示
- 展示模块和功能的层级关系

### Tab 2: 模块/功能描述管理（第二页）
- 展示模块和功能的描述信息
- 支持添加模块和功能（使用现有API）
- 支持删除模块和功能（使用现有API）
- 支持编辑模块/功能的描述
- 数据来源：`entry.data.description`

### Tab 3: 参数表格（第三页）
- 现有的参数表格（`ParameterTable`）
- 支持参数的增删改查
- 支持需求关联（已实现）

## Acceptance Criteria

- [ ] 架构页面显示3个Tab页：思维导图、模块/功能管理、参数表格
- [ ] Tab 1（思维导图）正确展示架构层级，不支持编辑
- [ ] Tab 2（模块/功能管理）展示模块和功能的描述
- [ ] Tab 2 支持添加模块和功能
- [ ] Tab 2 支持删除模块和功能
- [ ] Tab 2 支持编辑模块/功能的描述
- [ ] Tab 3（参数表格）保持现有功能不变
- [ ] 3个Tab页之间数据同步
- [ ] 响应式设计，支持移动端

## Notes

- 模块和功能数据来自 `parameterEntries` 的 `data.moduleName` 和 `data.featureName`
- 描述数据存储在 `entry.data.description`
- 添加/删除模块功能使用现有 `architectureService` API
