# 技术设计：修复 @xyflow/svelte 节点点击事件

## 问题分析

### 当前代码问题

`DynamicNode.svelte` 组件存在以下问题：

1. **缺少事件转发**：组件没有将点击事件转发给 @xyflow/svelte
2. **`class` 属性未传递**：外部传入的 `class` 属性没有被应用到节点容器
3. **Handle 组件可能阻止事件冒泡**：Handle 组件的默认行为可能拦截了节点点击

### @xyflow/svelte 事件机制

根据 @xyflow/svelte 文档：

- 节点选中通过 `on:select` 事件触发（Svelte 4）或 `onselect` 回调（Svelte 5）
- 自定义节点需要正确传递 `selected` 和 `selectable` 属性
- 节点容器需要能够接收点击事件

## 修复方案

### 方案 1：添加点击事件处理（推荐）

在节点容器上添加 `onclick` 事件处理，手动触发选中：

```svelte
<div
  class="..."
  onclick={() => {
    // 通过 SvelteFlow API 触发选中
  }}
>
```

### 方案 2：使用 SvelteFlowStore

通过 `useSvelteFlow` 获取 API，在点击时调用 `updateNode`：

```svelte
import { useSvelteFlow } from '@xyflow/svelte';
const { updateNodeData } = useSvelteFlow();
```

### 方案 3：检查节点配置

确保使用 `DynamicNode` 时，`selectable` 属性正确设置：

```typescript
const node = {
  id: '1',
  type: 'dynamic',
  selectable: true,  // 确保启用选中
  data: { ... }
};
```

## 技术决策

采用 **方案 1 + 方案 3** 的组合：

1. 在 `DynamicNode` 组件中确保 `selectable` 属性正确传递
2. 添加 `class` 属性传递，确保外部样式和事件可以应用
3. 检查 Handle 组件的事件处理，确保不阻止冒泡

## 兼容性考虑

- @xyflow/svelte 版本：需要确认当前版本的事件 API
- Svelte 5 语法：使用 `$props()` 和事件回调
- 不影响现有功能：Handle 拖拽、参数显示、可追溯性徽章
