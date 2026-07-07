# 执行计划：修复流程图模块三大问题

## 任务清单

### 任务 1: 修复流程图点击打开编辑器
- [ ] 检查 `openEntryEditor` 函数对 flowchart 类型的处理
- [ ] 确认 flowchart 列表项点击事件绑定正确
- [ ] 验证修复后点击能正常打开编辑器

### 任务 2: SVG 替换 ReactFlow
- [ ] 创建 SVG 版 `ReactFlowCanvas.svelte`
- [ ] 实现节点渲染（矩形、圆角、圆形、菱形、椭圆）
- [ ] 实现边线渲染（带箭头的贝塞尔曲线）
- [ ] 实现点击交互（节点点击、画布点击）
- [ ] 实现只读模式控制
- [ ] 测试与 `PMFlowchartEditor.svelte` 的兼容性

### 任务 3: 流程图列表显示版本信息
- [ ] 在 flowchart 列表项中添加版本标签
- [ ] 参考 architecture 模块实现版本显示逻辑
- [ ] 验证版本信息正确显示

## 执行顺序

1. 任务 1 和任务 3 可以并行（都修改 `+page.svelte`）
2. 任务 2 独立进行（修改 `ReactFlowCanvas.svelte`）
3. 最后统一测试

## 验证命令

```bash
# 构建检查
npm run build

# 类型检查
npx svelte-check
```

## 回滚点

- 如 SVG 实现有问题，可快速回滚到 `@xyflow/svelte` 版本
- 保持 git commit 原子性，每个任务独立提交
