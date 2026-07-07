# 设计文档：流程图模块修复

## 技术方案

### R1: 修复流程图点击打开编辑器

**问题分析**：
- 查看 `+page.svelte` 中 flowchart 模块的列表项渲染（约第 1874-1914 行）
- 列表项使用 `onclick={() => openEntryEditor(entry.id)}` 绑定点击事件
- 问题可能在于 `openEntryEditor` 函数未正确处理 flowchart 类型的编辑器

**修复方案**：
- 检查 `openEntryEditor` 函数中对 `flowchart` editorType 的处理逻辑
- 确保 flowchart 类型能正确打开编辑器面板

### R2: SVG 替换 ReactFlow

**当前实现**：
- `ReactFlowCanvas.svelte` 使用 `@xyflow/svelte` 的 `SvelteFlow`、`Background`、`Controls`、`MiniMap`
- 需要替换为纯 SVG 实现

**SVG 实现方案**：
- 使用 `<svg>` 元素作为画布
- 节点渲染：`<rect>`、`<circle>`、`<polygon>`（菱形）等 SVG 元素
- 边线渲染：`<path>` 元素，使用贝塞尔曲线
- 交互：SVG 元素的 `onclick` 事件
- 保持与 `ReactFlowCanvas` 相同的 Props 接口

**节点类型映射**：
| 形状 | SVG 元素 |
|------|---------|
| rectangle | `<rect>` |
| rounded | `<rect rx="12" ry="12">` |
| circle | `<circle>` |
| diamond | `<polygon>` |
| ellipse | `<ellipse>` |

**边线类型**：
- 使用 `<path>` 绘制平滑曲线（类似 smoothstep）
- 箭头标记使用 `<marker>`

### R3: 版本信息显示

**实现方案**：
- 参考 architecture 模块（第 1851-1858 行）
- 在 flowchart 列表项的右侧添加版本标签
- 使用 `getEntryData(entry, 'versionId')` 或 `entry.currentVersionNumber` 获取版本信息
- 样式：`bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-300` 圆角标签

## 文件变更

1. `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
   - 修复 flowchart 列表项点击事件
   - 添加版本信息显示

2. `src/lib/components/pm/reactflow/ReactFlowCanvas.svelte`
   - 完全替换为 SVG 实现

## 兼容性

- 保持 `ReactFlowCanvas` 的 Props 接口不变
- `PMFlowchartEditor.svelte` 无需修改（接口兼容）
- 数据格式保持兼容（nodes/edges 结构不变）
