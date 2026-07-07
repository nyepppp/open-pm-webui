# Implement: 架构图(D3)交互与信息展示

## 文件清单

| 文件 | 操作 |
|------|------|
| `src/lib/utils/excalidrawDataConverter.ts` | 修改 — 给模块节点添加 data |
| `src/lib/components/pm/mindmap/MindMapCanvas.svelte` | 修改 — 全部 6 项需求 |

## 执行顺序

### Step 1: treeToMindMap — 补模块节点 data
**文件**: `excalidrawDataConverter.ts`
**变更**: 模块节点增加 `data: { source: mod.source, featureCount: mod.features.length }`
**验证**: `lsp_diagnostics` clean
**回滚**: git checkout

### Step 2: 重构渲染架构 (R6 增量更新基础)
**文件**: `MindMapCanvas.svelte`
**变更**:
1. 分离 `init()` 和 `update()`
   - `init()`: 创建 SVG、zoom behavior、defs（glow filter）— 只执行一次
   - `update()`: 重新计算布局，用 data join 更新节点和连线
2. 引入 D3 data join 模式：
   - `g.selectAll('.link').data(treeData.links(), d => d.target.data.id)`
   - `g.selectAll('.node').data(treeData.descendants(), d => d.data.id)`
   - enter: 创建元素（透明起始）
   - update: 更新位置和属性
   - exit: 渐出后移除
3. 保存/恢复 zoom transform 跨更新
4. 添加 D3 transition (`duration: 400ms, ease: easeCubicOut`)
**验证**: 页面加载显示正常，zoom/pan 可用，数据变化后布局平滑过渡
**回滚**: git checkout

### Step 3: 布局优化 (R3)
**文件**: `MindMapCanvas.svelte`
**变更**:
1. 添加 `ResizeObserver`，`containerWidth` / `containerHeight` state
2. 修复 `layoutBilateralTree`：
   - 使用实际容器尺寸替代固定 1200×800
   - 交错分配左右节点（交替分配而非按前/后半）
   - 左右对称计算：左 `-(y + margin)`，右 `y + margin`
3. 确保 `$effect` 在 data 或容器尺寸变化时触发 update
**验证**: 窗口缩放后布局自适应，左右对称，功能/模块层级正确
**回滚**: git checkout

### Step 4: Tooltip (R1)
**文件**: `MindMapCanvas.svelte`
**变更**:
1. 模板添加 `<div>` tooltip container（绝对定位，pointer-events-none）
2. 定义 `TooltipState $state` 管理可见性、位置、内容
3. D3 node 绑定 `mouseenter` → 设置 tooltip 内容 + 位置
4. D3 node 绑定 `mouseleave` → 隐藏 tooltip
5. 防溢出逻辑：当 tooltip 超出视口时翻转到另一侧
6. Tooltip 内容：
   - 名称、类型标签、来源标识、参数数量、描述
**验证**: 悬停节点显示完整 tooltip，位置正确，防溢出有效
**回滚**: git checkout

### Step 5: 选中高亮 (R2)
**文件**: `MindMapCanvas.svelte`
**变更**:
1. `selectedNodeId $state` 管理选中
2. D3 node `click` → toggle 选中
3. 点击空白 → 取消选中（`svg.on('click', ...)` 过滤节点点击）
4. data join 的 update 部分根据选中状态应用样式：
   - 边框加粗 (stroke-width: 3→4)
   - 外发光 (SVG filter: `url(#selected-glow)`)
   - 颜色加深
5. 取消时恢复默认样式
**验证**: 点击节点高亮，再次点击取消，点击空白取消，选中节点视觉突出
**回滚**: git checkout

### Step 6: 来源标识 (R4)
**文件**: `MindMapCanvas.svelte`
**变更**:
1. 在每个 node group 内添加 `<circle>` 来源小圆点
2. data join 的 enter 阶段添加
3. 颜色：auto → `#3b82f6`（蓝），manual → `#22c55e`（绿）
4. 根节点隐藏
5. 位置：节点矩形右上角
**验证**: 自动/手动节点可见小圆点区分，颜色正确，暗黑模式可辨
**回滚**: git checkout

### Step 7: 自适应文字 (R5)
**文件**: `MindMapCanvas.svelte`
**变更**:
1. 用 SVG `<foreignObject>` 替代 `<text>` 渲染节点名称
2. foreignObject 尺寸 = `nodeWidth - 16` × `nodeHeight`
3. 内部 HTML `<div>` 使用 CSS `text-overflow: ellipsis`
4. 样式继承（字体、颜色、居中对齐）
5. 回退：如果 foreignObject 不兼容，保留 `<text>` + `getComputedTextLength()` 动态截断
**验证**: 长文本正确裁剪为 ...，CJK/英文混合正常，无文字溢出
**回滚**: git checkout

### Step 8: 整体验证
1. `lsp_diagnostics` 检查无新增错误
2. 所有交互功能正常：tooltip、点击选中、zoom/pan、自适应
3. 浅色/深色模式切换检查颜色可读性

## 验证命令

```bash
# LSP 诊断
lsp_diagnostics src/lib/components/pm/mindmap/MindMapCanvas.svelte
lsp_diagnostics src/lib/utils/excalidrawDataConverter.ts

# 语法检查
svelte-check || npx svelte-check

# 构建检查
npm run build 2>&1 | head -50
```

## 风险点

1. **foreignObject 兼容性**：某些浏览器/渲染环境不支持 SVG foreignObject → 需准备 `<text>` 回退方案
2. **data join key 函数**：`id` 必须唯一且稳定，否则节点动画异常
3. **ResizeObserver 频繁触发**：需 debounce 或使用 `requestAnimationFrame` 节流
4. **zoom 状态保存**：数据更新后重新计算 bounds 时可能覆盖用户手动 zoom
