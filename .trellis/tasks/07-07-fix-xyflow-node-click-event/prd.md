# 修复 @xyflow/svelte 节点点击事件问题

## Goal

修复 `DynamicNode.svelte` 组件中 @xyflow/svelte 节点点击事件无法正确触发的问题，确保用户可以正常选中节点。

## Requirements

### 问题描述

在流程图编辑器中，使用 @xyflow/svelte 的 `DynamicNode` 自定义节点组件时，点击节点无法触发选中状态（`selected` 属性不更新）。

### 根本原因分析

1. **缺少事件处理**：`DynamicNode` 组件没有正确处理 @xyflow/svelte 的节点点击事件
2. **事件可能被拦截**：`Handle` 组件可能阻止了事件冒泡
3. **`selectable` 属性未正确传递**：虽然默认值是 `true`，但需要确保在节点配置中正确设置
4. **缺少 `class` 属性传递**：外部传入的 `class` 属性可能包含必要的样式或事件处理

### 修复要求

1. 确保节点点击事件可以正确触发
2. 保持 `selectable` 属性正确传递
3. 确保 `class` 属性正确应用到节点容器
4. 不破坏现有的 Handle 功能（连接点拖拽）
5. 支持钻石形状和常规形状两种节点类型

## Acceptance Criteria

- [ ] 点击节点时，`selected` 状态正确更新
- [ ] 节点外观在选中时显示蓝色边框（`ring-2 ring-blue-400`）
- [ ] Handle（连接点）仍然可以正常拖拽创建连线
- [ ] 钻石形状节点和常规形状节点都能正常选中
- [ ] 不影响现有功能（参数显示、可追溯性徽章等）

## Notes

- 参考 @xyflow/svelte 官方文档中关于自定义节点的事件处理
- Svelte 5 使用 `onselect` 而非 `on:select` 语法
- 需要确保事件冒泡不被阻止
