# 修复流程图点击无响应 + 实现参数双向同步

## Goal

修复流程图编辑器中节点点击无响应的 bug，并实现 PRD AC5 中推迟的参数双向同步功能。

## Background

流程图模块 (issue #14) 已交付，但存在两个问题：
1. **Bug**: 点击流程图节点时 NodeConfigPanel 不弹出 — `on:nodeclick` 事件可能未正确触发或事件签名不匹配
2. **Missing Feature**: 参数双向同步 (PRD AC5) 被推迟，需要补全

## Requirements

### Bug 修复：节点点击无响应

- 点击流程图中的节点时，右侧 NodeConfigPanel 应弹出
- 点击空白处时，NodeConfigPanel 应关闭
- 点击不同节点时，NodeConfigPanel 应切换到新节点

### 功能补全：参数双向同步 (AC5)

1. **流程图 → 参数清单**：节点添加/移除参数关联时，更新参数清单条目的 `data.flowchartRefs` 字段
   - `flowchartRefs` 格式：`[{ flowchartId: string, nodeId: string, nodeLabel: string, type: 'input' | 'output' }]`
2. **参数清单 → 流程图**：参数条目被删除时，清理所有引用该参数的流程图节点
3. **参数清单表格**：在参数模块表格中新增"关联节点"列
   - 显示格式：`流程图标题 - 节点名称 (输入/输出)`
   - 支持多节点显示
   - 点击可跳转至对应流程图
4. **跨模块查询**：参数清单加载时，扫描当前项目所有 flowchart 类型条目，反向索引参数→节点的映射

## Acceptance Criteria

- [ ] 点击流程图节点弹出 NodeConfigPanel
- [ ] 点击空白处关闭 NodeConfigPanel
- [ ] 点击不同节点切换 NodeConfigPanel 内容
- [ ] 节点添加输入/输出参数时，参数清单条目同步更新 `flowchartRefs`
- [ ] 节点移除参数关联时，参数清单条目同步清理
- [ ] 参数清单表格显示"关联节点"列，格式正确
- [ ] 参数条目删除时，流程图节点同步清理关联
- [ ] 点击参数清单中的关联节点可跳转到流程图

## Out of Scope

- 自定义节点类型管理器（NodeTypeManager）
- 流程图导出为图片/PDF
- 自动布局算法

## Technical Notes

- `@xyflow/svelte@0.1.39` 事件系统可能需要调试 — 检查 `on:nodeclick` 的 event detail 签名
- 参数同步可以前端实现（无需后端事务），因为 ModuleEntry API 已支持完整 CRUD
- 反向索引在参数模块加载时构建（扫描 flowchart 条目），缓存到组件状态
