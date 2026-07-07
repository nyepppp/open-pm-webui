# 架构思维导图改用Excalidraw

## Goal

将架构页面的思维导图从 `PMMindMap` 组件改为使用 `ExcalidrawCanvas` 组件，以支持更灵活的绘图和展示。

## Requirements

### 功能需求
1. **展示架构图**：使用 Excalidraw 展示模块和功能的层级关系
2. **只读模式**：思维导图页面为只读模式，不支持编辑
3. **数据转换**：将 `aggregatedTree` 数据转换为 Excalidraw 的元素格式
4. **交互支持**：支持点击节点导航到对应的模块/功能

### 技术需求
1. 使用现有的 `ExcalidrawCanvas` 组件
2. 创建数据转换函数，将 `TreeModule[]` 转换为 Excalidraw 元素
3. 保持与现有架构数据结构的兼容性

## Acceptance Criteria

- [ ] 架构页面的思维导图Tab使用 Excalidraw 展示
- [ ] 正确展示模块和功能的层级关系
- [ ] 支持点击节点导航
- [ ] 只读模式，不支持编辑
- [ ] 与现有数据格式兼容

## Notes

- 使用 `ExcalidrawCanvas` 组件
- 需要创建 `treeToExcalidraw` 数据转换函数
- 参考 `flowchartToExcalidraw` 的实现方式
