# 修复架构图(D3)交互与信息展示

## Goal

增强架构思维导图（D3 树形图 `MindMapCanvas.svelte`）中模块和功能节点的交互反馈与信息展示，让用户可以直观地获取节点类型、来源、参数等上下文信息，并改善树形图布局和视觉效果。

## Background

当前架构页面的第一个 Tab（思维导图）使用 `MindMapCanvas.svelte` 组件，基于 D3.js `d3.tree()` 的双侧树布局（bilateral tree）展示模块和功能的层级关系。数据流：`architectureStore.aggregatedTree` → `treeToMindMap()` → `MindMapCanvas.data`。

当前存在以下问题：

### 1. 缺乏交互反馈
- 点击节点无选中高亮（只有 `onNodeClick` 回调，无视觉反馈）
- 无鼠标悬浮提示（无 tooltip）
- 无来源标识（自动/手动节点视觉无区别）

### 2. 信息展示不足
- 节点只显示 `name` 字段，无任何辅助信息
- 无版本信息在思维导图内
- 文本截断 `substring(0, 10) + '...'` 对 CJK 字符不友好（10个汉字在 140px 宽节点内显示正常，但标点/英文混合时浪费空间）

### 3. 布局问题
- 固定宽高 `width=1200, height=800` 不响应容器尺寸
- 双侧布局不对称：左节点用 `-node.y - 100`（镜像翻倍原树宽度），右节点用 `node.y + 100`（仅加 100），导致左右两侧不对称
- 每次数据变化全量重渲染（`selectAll('*').remove()`），破坏 zoom 状态

### 4. 可访问性问题
- 节点无 `title` 属性，无 ARIA 标注
- 颜色仅按类型区分（root=蓝, module=绿, feature=黄），但对色盲用户不友好

## Requirements

### R1: 节点信息提示 (Tooltip)
- 用户悬停模块或功能节点时，显示包含以下信息的 tooltip:
  - 节点名称（完整，不截断）
  - 节点类型（模块/功能）
  - 来源（自动分析/手动创建）- 从 `data.source` 读取
  - 参数数量 - 从 `data.paramCount` 读取
  - 描述（如果有，从 `data.description` 读取，最多显示 3 行）
- Tooltip 样式：深色背景、圆角、阴影，跟随鼠标位置

### R2: 选中高亮
- 点击节点时，该节点获得视觉高亮（边框颜色变深、阴影、外发光）
- 同一时间只有一个选中节点
- 再次点击同一个节点取消选中
- 点击背景空白区域取消选中
- 选中状态通过 `$state` 管理，保留选中节点引用

### R3: 布局优化
- 使用 `ResizeObserver` 监听容器尺寸变化，自适应宽高
- 左右两侧对称布局：左右节点距离根节点的水平距离应一致
- 添加过渡动画（节点展开/收起使用 D3 transition）

### R4: 来源标识
- 自动来源节点：在右上角添加小圆点标识（蓝色）
- 手动来源节点：添加小圆点标识（绿色）
- 节点边框样式微调以区分来源

### R5: 自适应文字
- 根据节点宽度动态计算截断长度
- 英文/数字与 CJK 混合时，用实际渲染宽度而非字符计数
- 使用 SVG `<foreignObject>` 或 CSS `text-overflow: ellipsis` 配合合适字体

### R6: 增量更新（性能）
- 数据变化时保留 zoom 状态和 transform
- 使用 D3 的 data join（update/enter/exit）而非全量 `remove()`
- 支持在数据变化时做平滑过渡

## Acceptance Criteria

- [ ] R1: 悬停模块/功能节点显示 tooltip，包含名称、类型、来源、参数数量、描述
- [ ] R1: Tooltip 深色圆角风格，跟随鼠标位置，不溢出视口
- [ ] R2: 点击节点有可视选中高亮（边框加粗 + 阴影 + 外发光）
- [ ] R2: 再次点击选中节点取消选中，点击背景取消选中
- [ ] R3: 思维导图随容器自动调整大小（ResizeObserver）
- [ ] R3: 左右两侧布局对称，节点等距分布
- [ ] R3: 布局变化有平滑过渡动画
- [ ] R4: 自动来源节点和手动来源节点有区分度 >= 2 种视觉标识
- [ ] R5: 节点文字自适应，不出现文字溢出或过多截断
- [ ] R6: zoom 状态在数据更新后保持
- [ ] 所有颜色在浅色/深色模式下都清晰可辨
- [ ] `lsp_diagnostics` 无新增错误

## Technical Notes

- 核心文件：`src/lib/components/pm/mindmap/MindMapCanvas.svelte`
- 数据来源：`architectureStore.aggregatedTree` (通过 `treeToMindMap` 转换为 `TreeNode`)
- TreeNode 类型已包含 `data` 字段（`data.source`, `data.paramCount`, `data.description`）
- 当前使用 Svelte 5 `$state` + `$effect` + D3 v7
- 文字渲染使用 SVG `<text>`，限制在 140px 宽区域内
- 布局算法在 `layoutBilateralTree()` 函数中

## Out of Scope

- 不在思维导图中添加编辑功能（增删改模块/功能走 Tab 2）
- 不改变 Tab 切换逻辑
- 不更改 `treeToMindMap` 数据转换函数的结构
- 不改动 `ModuleFeatureManager.svelte`（Tab 2 的模块/功能管理）
- Excalidraw 流程图相关的任何修改

## User Decisions

- 2026-07-07: 用户确认全部 6 个需求（R1-R6）一起做，不拆分。

## Open Questions

（无——所有问题均可通过代码检查确定）
