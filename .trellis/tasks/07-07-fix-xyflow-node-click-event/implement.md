# 执行计划：修复 @xyflow/svelte 节点点击事件

## 执行步骤

### Step 1: 分析当前代码

读取 `DynamicNode.svelte` 和相关文件，确认：
- 当前 `selectable` 属性的传递方式
- Handle 组件的使用方式
- 节点在父组件中的配置方式

### Step 2: 修复 DynamicNode.svelte

修改 `src/lib/components/pm/flowchart/DynamicNode.svelte`：

1. **添加 `class` 属性传递**：
   ```svelte
   let { id, data, selected, selectable = true, class: className = '' }: NodeProps = $props();
   ```

2. **确保事件可以触发**：
   - 检查是否需要添加 `pointer-events: auto` 或类似样式
   - 确保 Handle 组件不阻止事件冒泡

3. **应用 `class` 到容器**：
   ```svelte
   <div class="{containerClass} {className} {selected ? 'ring-2 ring-blue-400' : ''}">
   ```

### Step 3: 检查节点配置

在 `PMFlowchartEditor.svelte` 或相关文件中，确保节点配置：

```typescript
{
  id: '...',
  type: 'dynamic',
  selectable: true,  // 明确启用选中
  data: { ... }
}
```

### Step 4: 验证修复

1. 启动开发服务器
2. 打开流程图编辑器
3. 测试点击节点：
   - 常规形状节点
   - 钻石形状节点
   - 带 Handle 的节点
4. 验证选中状态变化
5. 验证 Handle 拖拽功能正常

## 验证命令

```bash
# 启动开发服务器
npm run dev

# 或者构建检查
npm run build
```

## 回滚点

如果修复引入新问题，回滚到修改前的 `DynamicNode.svelte`：

```bash
git checkout src/lib/components/pm/flowchart/DynamicNode.svelte
```

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| Handle 拖拽受影响 | 确保 Handle 组件的 `pointer-events` 正确设置 |
| 样式冲突 | 使用 `class` 属性传递，不覆盖现有样式 |
| 性能影响 | 最小化修改，不添加不必要的计算 |
