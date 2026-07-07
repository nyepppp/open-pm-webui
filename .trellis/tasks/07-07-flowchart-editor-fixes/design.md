# 流程图编辑器缺陷修复 - 技术设计

## Architecture

### 整体架构

```
PMFlowchartEditor.svelte (Svelte 5)
├── ExcalidrawCanvas.svelte (Svelte-React 桥接)
│   └── Excalidraw (React 组件)
│       ├── 画布 (自由绘制)
│       ├── 工具栏 (形状/箭头/文本)
│       └── 属性面板
├── NodeConfigPanel.svelte (节点配置)
│   └── 参数绑定/可追溯性
├── TraceabilitySidebar.svelte (溯源侧边栏)
│   └── EntityBindingPanel.svelte (实体绑定)
└── DataConverter (数据转换层)
    ├── FlowchartData → Excalidraw JSON
    └── Excalidraw JSON → FlowchartData
```

## 问题分析与修复方案

### 问题 1: 节点形状创建受限

**根因**: `excalidrawDataConverter.ts` 中的 `flowchartToExcalidraw` 函数虽然根据 `node.type` 映射了不同的 Excalidraw 形状（ellipse, diamond, rectangle），但 Excalidraw 本身对 `type` 字段的支持有限。Excalidraw 实际支持的形状类型需要通过 `strokeRoundness` 或其他属性来控制。

**修复方案**:
1. 检查 Excalidraw 实际支持的元素类型
2. 对于不支持原生菱形/椭圆的情况，使用 `roughness` 和 `strokeRoundness` 属性模拟
3. 确保 `excalidrawToFlowchart` 能正确识别和还原形状

### 问题 2: 节点配置面板未融入 Excalidraw 交互

**根因**: 
1. `ExcalidrawCanvas.svelte` 使用 `onPointerDown` 事件捕获元素点击，但事件处理可能不稳定
2. `PMFlowchartEditor.svelte` 中的 `handleElementClick` 和 `updateNodeData` 函数逻辑需要完善
3. 配置面板弹出后，修改形状等属性后无法同步回 Excalidraw

**修复方案**:
1. 改进 ExcalidrawCanvas 的事件监听机制
2. 完善 `updateNodeData` 函数，支持更新 Excalidraw 元素的形状、颜色等属性
3. 确保配置面板关闭后状态正确清理

### 问题 3: 溯源绑定功能失效

**根因**: 
1. `TraceabilitySidebar.svelte` 和 `EntityBindingPanel.svelte` 的 props 传递可能存在问题
2. 绑定信息保存到 `customData` 的逻辑需要验证

**修复方案**:
1. 检查 props 传递链
2. 验证 `customData.traceability` 的读写逻辑
3. 添加错误处理和用户反馈

### 问题 4: 导出功能缺失

**根因**: 
1. `PMFlowchartEditor.svelte` 中只有 `exportToPNG` 和 `exportToSVG` 的基础实现
2. SVG 导出实现不完整（使用了 canvas.toDataURL 而非真正的 SVG）
3. 缺少 Markdown 和 drawio 格式的导出

**修复方案**:
1. 完善 PNG 导出（利用 Excalidraw 原生 API）
2. 实现真正的 SVG 导出
3. 实现 Markdown 导出（文本描述流程图结构）
4. 实现 drawio 导出（生成 XML 格式）

## 数据流

```
用户交互
  ↓
Excalidraw 画布
  ↓
onChange / onElementClick 事件
  ↓
PMFlowchartEditor 处理
  ↓
更新 selectedElement / selectedNodeData
  ↓
显示 NodeConfigPanel / TraceabilitySidebar
  ↓
用户修改配置
  ↓
updateNodeData → Excalidraw API updateScene
  ↓
onChange → excalidrawToFlowchart → onChange
  ↓
保存到后端
```

## 关键修改点

### 1. excalidrawDataConverter.ts

- `flowchartToExcalidraw`: 确保形状映射正确
- `excalidrawToFlowchart`: 确保形状信息不丢失
- 添加形状验证辅助函数

### 2. ExcalidrawCanvas.svelte

- 改进事件监听机制
- 暴露更多 API 方法（updateScene, getSceneElements 等）
- 支持动态更新元素属性

### 3. PMFlowchartEditor.svelte

- 完善 `handleElementClick` 和 `updateNodeData`
- 添加导出功能（PNG, SVG, Markdown, drawio）
- 优化面板显示逻辑

### 4. NodeConfigPanel.svelte

- 确保形状选择能正确更新 Excalidraw 元素
- 验证参数绑定逻辑

### 5. TraceabilitySidebar.svelte / EntityBindingPanel.svelte

- 修复 props 传递
- 验证绑定保存逻辑

## 回滚方案

如需回滚：
1. 保留当前修改的 git 分支
2. 回滚到上一个稳定版本

## 性能考虑

- Excalidraw 画布渲染性能良好
- 数据转换在客户端进行，不影响后端性能
- 导出功能在后台执行，不阻塞 UI
