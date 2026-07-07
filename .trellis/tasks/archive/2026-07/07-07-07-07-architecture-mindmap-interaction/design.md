# Design: 架构图(D3)交互与信息展示

## 架构概览

```
MindMapCanvas.svelte (单个组件)
├── D3 树形布局 (layoutBilateralTree)
├── SVG 渲染 (render)
│   ├── 连线 (path.link)
│   ├── 节点 (g.node)
│   │   ├── rect (背景 + 边框)
│   │   ├── text (名称)
│   │   └── circle (来源标识)  [NEW]
│   └── 版本标签 (text)
├── Tooltip (HTML div overlay)  [NEW]
├── 选中状态管理  [NEW]
└── ResizeObserver  [NEW]
```

数据流：
```
architectureStore.aggregatedTree (TreeModule[])
  → treeToMindMap() (excalidrawDataConverter.ts)
    → MindMapCanvas.data (TreeNode)
      → d3.hierarchy → d3.tree → layoutBilateralTree
        → SVG render
```

## R1: Tooltip (信息提示)

### 方案
使用 HTML `<div>` overlay（非 SVG）实现 tooltip，避免 SVG 的渲染限制。

- **创建**：在组件模板中添加 `<div>` 绝对定位容器
- **显示触发**：D3 node group 的 `mouseenter` 事件 → 设置 tooltip 内容 + 位置
- **隐藏触发**：`mouseleave` 事件
- **位置计算**：基于鼠标相对于 `container` 的 offset，自动防溢出（贴近视口边缘时翻转到另一侧）
- **内容**：
  - 节点名称（完整，不截断）
  - 类型标签（模块/功能）
  - 来源（自动/手动）+ 颜色标识
  - 参数数量（功能节点）
  - 描述（如果有）
- **样式**：深色背景 (`bg-gray-900/90`)、白色文字、圆角、阴影、z-50

### Tooltip 数据结构
```typescript
interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  content: {
    name: string;
    type: string;
    source: 'auto' | 'manual';
    paramCount?: number;
    description?: string;
  };
}
```

## R2: 选中高亮

### 方案
Svelte `$state` 管理选中节点，D3 渲染时根据选中状态动态应用样式。

- **状态**：`selectedNodeId: string | null`
- **触发**：D3 node `click` → toggle `selectedNodeId`
- **取消**：点击空白区域或再次点击同一节点
- **视觉**：
  - 边框加粗 (stroke-width 3→4)
  - 外发光 (SVG filter: drop-shadow)
  - 选中框颜色加深
- **更新策略**：选中变化时用 D3 selection 直接更新样式，不触发全量重渲染

### SVG filter for glow
```svg
<filter id="selected-glow">
  <feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="#3b82f6" flood-opacity="0.5"/>
</filter>
```

## R3: 布局优化

### 方案
使用 `ResizeObserver` 监听容器实际尺寸，动态计算布局参数。修复双侧布局对称性。

### ResizeObserver
```typescript
let containerWidth = $state(1200);
let containerHeight = $state(800);

const ro = new ResizeObserver(entries => {
  const { width, height } = entries[0].contentRect;
  containerWidth = width;
  containerHeight = height;
});
```

### 对称双侧布局算法
1. `d3.tree().size([treeHeight, treeWidth / 2 - spacing])` — 用半宽计算树布局
2. 根节点子节点按原 y 排序
3. 交错分配左右（alternating）：第 0,2,4...个 → 左；第 1,3,5...个 → 右
4. 左侧节点：`y = -(y + margin)`（镜像到左侧）
5. 右侧节点：`y = y + margin`（保持在右侧）
6. 根节点 `y = 0`，水平居中

### 过渡动画
- D3 `transition().duration(400).ease(d3.easeCubicOut)`
- 节点移动、连线和节点进入/退出都有动画

## R4: 来源标识

### 方案
在节点矩形右上角添加 SVG `<circle>` 小圆点。

- 自动 (auto)：蓝色小圆点 `#3b82f6`
- 手动 (manual)：绿色小圆点 `#22c55e`
- 根节点不显示
- 圆点位置：节点矩形右上角 (x: +nodeWidth/2 - 6, y: -nodeHeight/2 + 6)
- 圆点尺寸：r=5

## R5: 自适应文字

### 方案
使用 SVG `<foreignObject>` 包裹 HTML `<div>` 实现原生 CSS 文字截断。

- `<foreignObject width={nodeWidth - 20} height={nodeHeight}>`
- `<div style="width: 100%; height: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{name}</div>`
- 字体大小保持 12px，但根据内容长度可通过 CSS 调整

**回退方案**：如果 `foreignObject` 有兼容性问题，继续使用 SVG `<text>`，但用 `getComputedTextLength()` 动态计算截断长度。

## R6: 增量更新

### 方案
重构 `render()` 函数，使用 D3 的 data join 模式（enter/update/exit），避免全量 `remove()`。

### 当前问题
```typescript
// 每次数据变化：
d3.select(container).selectAll('*').remove();  // 清除所有
// 重建 SVG、zoom、所有节点和连线
```

### 新架构
```typescript
function update() {
  // 1. 如果 SVG/zoom 还不存在 → 初始化（首次）
  // 2. 重新计算 layout（数据可能变了）
  // 3. Data join 连线: g.selectAll('.link').data(newLinks)
  //    - enter: 新增连线（透明→可见动画）
  //    - update: 更新路径
  //    - exit: 淡出→移除
  // 4. Data join 节点: g.selectAll('.node').data(newNodes)
  //    - enter: 新增节点
  //    - update: 更新位置、文字、样式
  //    - exit: 淡出→移除
  // 5. 保持 zoom.transform 不变
}
```

### 状态分离
- **初始化 (init)**：创建 SVG、zoom behavior、defs（filter等）— 只执行一次
- **更新 (update)**：数据变化时更新布局和节点 — 保留 zoom 状态

## 文件变更

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `src/lib/components/pm/mindmap/MindMapCanvas.svelte` | 修改 | 全部 6 项需求 |
| `src/lib/utils/excalidrawDataConverter.ts` | 修改 | 给模块节点补 `data` 字段 |
