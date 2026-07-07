# Excalidraw 集成设计文档

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
└── DataConverter (数据转换层)
    ├── FlowchartData → Excalidraw JSON
    └── Excalidraw JSON → FlowchartData
```

### 组件设计

#### 1. ExcalidrawCanvas.svelte

**职责**：Svelte-React 桥接组件，封装 Excalidraw 实例

**Props**：
```typescript
interface ExcalidrawCanvasProps {
  initialData?: ExcalidrawInitialDataState;
  onChange?: (elements: ExcalidrawElement[], appState: AppState) => void;
  onElementClick?: (element: ExcalidrawElement) => void;
  theme?: 'light' | 'dark';
  viewModeEnabled?: boolean;
  gridModeEnabled?: boolean;
}
```

**实现要点**：
- 使用 `react-dom/client` 的 `createRoot()` 在 Svelte 生命周期中创建 React 根
- 通过 `$effect()` 监听 props 变化并同步到 React 组件
- 暴露 `excalidrawAPI` 供父组件调用

#### 2. PMFlowchartEditor.svelte (重写)

**职责**：流程图编辑器主组件，协调 Excalidraw 画布和业务逻辑

**状态管理**：
```typescript
interface FlowchartEditorState {
  flowchartData: FlowchartData;
  selectedElement: ExcalidrawElement | null;
  showConfigPanel: boolean;
  showTraceabilityPanel: boolean;
  theme: 'light' | 'dark';
}
```

**核心逻辑**：
1. 加载时：`FlowchartData` → `Excalidraw JSON` → 渲染画布
2. 编辑时：监听 Excalidraw `onChange` → 转换为 `FlowchartData` → 触发 `onChange`
3. 保存时：当前 `FlowchartData` → 后端 API

#### 3. DataConverter (数据转换层)

**职责**：在 `FlowchartData` 和 `Excalidraw JSON` 之间转换

**转换规则**：

| FlowchartData | Excalidraw JSON |
|--------------|----------------|
| 节点 (node) | 形状元素 (rectangle/ellipse/diamond) |
| 边 (edge) | 箭头元素 (arrow) |
| 节点标签 | 文本元素绑定到形状 |
| 节点类型 | `customData.type` |
| 节点描述 | `customData.description` |
| 输入参数 | `customData.inputParams` |
| 输出参数 | `customData.outputParams` |
| 可追溯性 | `customData.traceability` |

### 数据流

```
后端 API
  ↓
FlowchartData (现有格式)
  ↓
DataConverter.toExcalidraw()
  ↓
Excalidraw JSON
  ↓
Excalidraw 画布渲染
  ↓
用户编辑
  ↓
Excalidraw onChange
  ↓
DataConverter.toFlowchart()
  ↓
FlowchartData
  ↓
后端 API
```

### 样式映射

**节点类型 → Excalidraw 形状**：

| 节点类型 | Excalidraw 形状 | 颜色 |
|---------|----------------|------|
| start | ellipse | #dcfce7 (浅绿) |
| end | ellipse | #fee2e2 (浅红) |
| decision | diamond | #fef9c3 (浅黄) |
| process | rectangle | #dbeafe (浅蓝) |
| parameter-input | rectangle | #f3e8ff (浅紫) |
| parameter-output | rectangle | #fce7f3 (浅粉) |

**边样式**：
- 默认：实线箭头
- 条件分支：虚线箭头（可选）

## Compatibility & Migration

### 向后兼容
- 现有 `FlowchartData` 数据格式保持不变
- 新增 `excalidrawData` 字段存储 Excalidraw 原生格式（可选）
- 如果没有 `excalidrawData`，使用 `FlowchartData` 转换渲染

### 数据迁移
- 现有数据无需迁移，通过 `DataConverter` 实时转换
- 保存时同时存储 `FlowchartData` 和 `excalidrawData`

## Rollback

如需回滚到 `@xyflow/svelte`：
1. 保留原有 `PMFlowchartEditor.svelte` 为 `PMFlowchartEditor.xyflow.svelte`
2. 切换时恢复原有组件即可

## Performance Considerations

- React 运行时增加 ~40KB bundle
- 数据转换在客户端进行，不影响后端性能
- Excalidraw 画布渲染性能良好（基于 Canvas）
