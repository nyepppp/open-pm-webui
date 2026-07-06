# 需求模块归属 + 新增模块定位

## Goal

明确需求页面中新增模块的归属问题——新功能应该放在产品架构图还是参数配置模块中。

## Context

- **Issue 原文**: "是不是应该新增个模块。这个功能应该放在产品架构图，还是参数那块？"
- **当前结构**: requirement（需求管理）是一个独立的 table 模块，有 source/category/userRole 等字段
- **产品架构** (product-architecture): 思维导图编辑器
- **参数配置** (parameter): table 编辑器，含 moduleName/featureName 分层

## Decision

归属产品架构。在产品架构思维导图中增加"模块"节点类型，作为一级节点。

## Requirements

1. 在产品架构思维导图中增加"模块"节点类型
2. 模块作为一级节点，功能为二级，参数为三级
3. 模块节点可在思维导图中创建和管理

## Acceptance Criteria

- [ ] 产品架构思维导图支持"模块"节点类型
- [ ] 模块节点可作为一级节点创建
- [ ] 模块→功能→参数三级结构可展示

## Notes

- 用户决策：归属产品架构
- 优先级较低，待其他 bug 修复后推进
