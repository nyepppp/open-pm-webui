# Design: 架构可视化优化

## 1. 思维导图组件替换

### 当前方案
- 使用 `@excalidraw/excalidraw` React 组件
- 通过 `excalidrawDataConverter.ts` 转换数据
- 问题：连线样式不美观，不是专门的 mindmap

### 新方案
使用 `d3` 或专门的 mindmap 库：

**选项 A: 自定义 D3 Mindmap**
- 优点：完全可控，可定制性强
- 缺点：开发成本高
- 实现：使用 d3-hierarchy + d3-tree 布局

**选项 B: 使用现有库**
- `markmap` - Markdown 思维导图，不适合
- `react-flow` - 流程图，可定制为树形
- `d3-mindmap` - 专门的 mindmap 库

**推荐**: 选项 A - 自定义 D3 实现
- 使用 `d3-hierarchy` 进行树形布局计算
- 使用 SVG 绘制节点和连线
- 支持缩放、拖拽、点击交互

### 数据结构
```typescript
interface MindMapNode {
  id: string;
  name: string;
  type: 'root' | 'module' | 'feature';
  children?: MindMapNode[];
  data?: any;
}
```

### 组件设计
```
MindMapCanvas
├── SVG Container
│   ├── Links (Bezier curves)
│   └── Nodes
│       ├── Root Node (产品)
│       ├── Module Nodes
│       └── Feature Nodes
└── Controls (Zoom, Fit)
```

## 2. 模块卡片布局

### 当前方案
- 使用 `<table>` 展示模块/功能
- 层级通过展开/收起实现

### 新方案
卡片式布局，层层递进：

```
ModuleCardsContainer
├── ModuleCard x N
│   ├── Header (名称 + 来源 + 功能数)
│   ├── Description
│   └── FeatureCards (展开时)
│       ├── FeatureCard x M
│       │   ├── Header (名称 + 来源 + 参数数)
│       │   ├── Description
│       │   └── ParameterTable (展开时)
│       └── AddFeatureButton
└── AddModuleButton
```

### 样式设计
- **ModuleCard**: 圆角卡片，阴影，hover 效果
- **FeatureCard**: 内嵌卡片，缩进显示
- **ParameterTable**: 保持现有表格样式

### 暗黑模式
- 使用 Tailwind dark: 前缀
- 卡片背景：dark:bg-gray-800
- 文字：dark:text-gray-100

## 3. 数据流

保持现有数据流不变：
- `architectureStore` - 状态管理
- `architectureService` - API 调用
- `excalidrawDataConverter` - 数据转换（需更新）

## 4. 交互设计

### MindMap
- 点击节点：选中并高亮
- 双击节点：编辑（如果可编辑）
- 拖拽：平移画布
- 滚轮：缩放

### ModuleCards
- 点击模块卡片：展开/收起功能列表
- 点击功能卡片：展开/收起参数表格
- 编辑描述：点击编辑按钮，显示 textarea
- 删除：点击删除按钮，确认后删除
