# 集成 Excalidraw 作为流程图画布编辑器

## Goal

将项目中的流程图编辑器从 `@xyflow/svelte` 迁移到 `Excalidraw`，提供真正的自由画布编辑体验，支持手绘风格的流程图绘制。

## Background

当前项目使用 `@xyflow/svelte` (v0.1.19) 实现流程图功能，基于 node-edge 模型，用户反馈"没做好"，希望获得自由画布编辑体验。

经过调研，Excalidraw 是最佳选择：
- 真正的自由画布（free canvas），非 node-edge 模型
- 手绘风格，用户体验好
- 功能丰富：形状、箭头、文本、自由绘制
- 导出完善：PNG/SVG/JSON
- 社区活跃（~80K stars）

Excalidraw 是 React 组件，需要通过桥接层在 Svelte 5 中使用。

## Requirements

### 功能需求
- [R1] 安装并配置 Excalidraw 依赖（react, react-dom, @excalidraw/excalidraw）
- [R2] 创建 Svelte-React 桥接组件 `ExcalidrawCanvas.svelte`
- [R3] 重写 `PMFlowchartEditor.svelte`，使用 Excalidraw 替代 @xyflow/svelte
- [R4] 创建数据转换层：`FlowchartData` ↔ Excalidraw JSON 格式互转
- [R5] 支持现有节点类型在 Excalidraw 中的渲染（开始/结束/判断/处理/参数输入/参数输出）
- [R6] 保留节点配置面板（标签、描述、参数绑定）
- [R7] 保留可追溯性侧边栏功能
- [R8] 支持数据保存/加载，与现有后端 API 兼容
- [R9] 支持导出功能（PNG/SVG/JSON）
- [R10] 支持暗色模式

### 非功能需求
- [R11] 保持与现有 `FlowchartData` 数据格式的向后兼容
- [R12] 键盘快捷键支持（Delete 删除选中元素）
- [R13] 响应式布局，适配不同屏幕尺寸

## Acceptance Criteria

- [ ] `npm install react react-dom @excalidraw/excalidraw` 成功安装
- [ ] `ExcalidrawCanvas.svelte` 桥接组件正常工作，无控制台错误
- [ ] 流程图编辑器正常渲染 Excalidraw 画布
- [ ] 支持自由绘制流程图（形状、箭头、文本）
- [ ] 支持从现有 `FlowchartData` 加载并渲染为 Excalidraw 格式
- [ ] 支持将 Excalidraw 数据保存为现有 `FlowchartData` 格式
- [ ] 节点配置面板正常工作（点击元素弹出配置）
- [ ] 可追溯性侧边栏正常工作
- [ ] 导出 PNG/SVG/JSON 功能正常
- [ ] 暗色模式支持
- [ ] 键盘快捷键（Delete 删除）正常工作
- [ ] 现有流程图数据向后兼容（旧数据可以正常加载）

## Out of Scope

- 实时协作编辑
- Mermaid 语法导入（Excalidraw 原生支持，但不在本次集成范围内）
- 自定义 Excalidraw 库（libraries）
- 手写识别/AI 辅助绘图

## Technical Notes

### 桥接方案
使用 Svelte 5 的 `$effect()` 和 `react-dom/client` 创建 React-in-Svelte 桥接。

### 数据转换
**FlowchartData → Excalidraw JSON**：节点 → 形状元素，边 → 箭头元素
**Excalidraw JSON → FlowchartData**：形状元素 → 节点，箭头元素 → 边

### 依赖
- `react` (^18.x 或 ^19.x)
- `react-dom` (^18.x 或 ^19.x)
- `@excalidraw/excalidraw` (^0.18.x)

### 风险
- React 运行时增加 bundle 体积（~40KB+）
- Svelte 5 与 React 19 的兼容性需验证
- 数据转换层可能丢失部分样式信息
