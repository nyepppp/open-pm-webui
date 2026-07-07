# 修复流程图编辑器多项缺陷

## Goal

修复 Excalidraw 流程图编辑器中的关键缺陷，提升用户体验，确保节点配置、溯源绑定、导出功能等核心能力正常工作。

## Background

当前流程图编辑器已完成从 `@xyflow/svelte` 到 Excalidraw 的迁移，但存在以下关键缺陷影响使用：

1. **节点形状创建受限**：Excalidraw 原生支持矩形、圆形、菱形等多种形状，但当前转换层将所有节点统一映射为矩形，用户无法创建标准流程图形状
2. **节点配置面板未融入 Excalidraw 交互**：点击 Excalidraw 元素时配置面板无法正确弹出，配置修改后无法同步回画布
3. **溯源绑定功能失效**：溯源侧边栏无法正常显示和绑定实体
4. **导出功能缺失**：不支持导出为 drawio 或 markdown 格式

## Requirements

### R1: 支持多种节点形状创建
- Excalidraw 原生支持矩形、圆形、菱形、椭圆等形状
- 数据转换层 (`excalidrawDataConverter.ts`) 需正确映射节点类型到对应形状
- 节点配置面板中的形状选择需能正确修改 Excalidraw 元素形状

### R2: 节点配置面板融入 Excalidraw 交互
- 点击 Excalidraw 元素时正确弹出配置面板
- 配置面板修改后同步更新 Excalidraw 画布
- 支持通过 Excalidraw 工具栏直接创建带类型的流程图节点

### R3: 溯源绑定功能修复
- 溯源侧边栏正常显示当前绑定状态
- 支持搜索和选择实体进行绑定
- 绑定信息正确保存到节点 customData

### R4: 导出功能实现
- 支持导出为 PNG/SVG（利用 Excalidraw 原生导出能力）
- 支持导出为 Markdown 格式（文本描述流程图）
- 支持导出为 drawio 格式（XML 格式兼容 draw.io）

### R5: 工作台分页问题
- 工作台模块列表超过 20 条时进行分页

### R6: 架构页面性能优化
- 思维导图渲染性能优化
- 模块结构展示优化

## Acceptance Criteria

- [ ] 用户可以在 Excalidraw 中创建矩形、圆形、菱形、椭圆等多种形状的节点
- [ ] 点击 Excalidraw 元素时节点配置面板正确弹出
- [ ] 修改节点配置（标签、描述、形状、颜色）后画布实时更新
- [ ] 溯源绑定功能正常工作：搜索实体 → 选择绑定 → 保存 → 显示绑定状态
- [ ] 支持导出为 PNG、SVG、Markdown、drawio 格式
- [ ] 工作台模块列表超过 20 条时自动分页
- [ ] 架构页面思维导图渲染流畅，布局正确

## Out of Scope

- 实时协作编辑
- AI 辅助绘图
- 手写识别

## Technical Notes

### 关键文件
- `src/lib/components/pm/PMFlowchartEditor.svelte` - 流程图编辑器主组件
- `src/lib/components/pm/excalidraw/ExcalidrawCanvas.svelte` - Excalidraw 桥接组件
- `src/lib/utils/excalidrawDataConverter.ts` - 数据转换层
- `src/lib/components/pm/flowchart/NodeConfigPanel.svelte` - 节点配置面板
- `src/lib/components/pm/flowchart/TraceabilitySidebar.svelte` - 溯源侧边栏
- `src/lib/components/pm/flowchart/EntityBindingPanel.svelte` - 实体绑定面板

### 已知问题
- `excalidrawDataConverter.ts` 中 `flowchartToExcalidraw` 函数将节点类型映射为 Excalidraw 形状，但 `excalidrawToFlowchart` 反向转换时丢失了形状信息
- ExcalidrawCanvas 的 `onPointerDown` 事件处理可能无法正确捕获元素点击
- 导出功能目前只有 PNG 的基础实现，SVG 导出实现不完整
