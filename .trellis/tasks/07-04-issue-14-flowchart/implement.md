# 流程图模块执行计划

## 实施步骤

### Phase 1: 数据模型与类型定义

- [ ] 1.1 在 `src/lib/apis/pm/types.ts` 中新增 `flowchart` 到 `ModuleType` 联合类型
- [ ] 1.2 新增 FlowchartData 相关类型定义（FlowchartNode, FlowchartEdge）
- [ ] 1.3 在 `src/lib/apis/pm/modules/` 下创建 `flowchart.ts` API 文件

### Phase 2: 模块配置集成

- [ ] 2.1 在 `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` 的 `moduleConfig` 中新增 flowchart 配置
- [ ] 2.2 在 `src/lib/components/pm/moduleFields.ts` 中新增 flowchart 字段配置
- [ ] 2.3 在导航菜单配置中新增 flowchart 入口

### Phase 3: 流程图编辑器组件

- [ ] 3.1 创建 `src/lib/components/pm/flowchart/FlowchartCanvas.svelte` - SvelteFlow 画布容器
- [ ] 3.2 创建动态节点渲染器 `src/lib/components/pm/flowchart/nodes/DynamicNode.svelte`
  - 根据 node.data.style.shape 动态渲染不同形状（矩形、圆角、圆形、菱形、椭圆）
  - 支持样式覆盖（颜色、边框、大小）
- [ ] 3.3 创建 `src/lib/components/pm/flowchart/NodePanel.svelte` - 节点工具栏
  - 预设节点模板（开始、处理、判断、结束）
  - 自定义节点类型管理（创建、编辑、删除）
- [ ] 3.4 创建 `src/lib/components/pm/flowchart/NodeConfigPanel.svelte` - 节点属性配置
  - 基础属性：名称、描述
  - 样式编辑器：颜色选择器、边框设置、形状选择、大小调整
  - 参数选择器（关联参数清单）
- [ ] 3.5 创建 `src/lib/components/pm/flowchart/CustomEdge.svelte` - 支持样式的自定义连线
  - 实线/虚线切换
  - 颜色、粗细设置
  - 动画效果
- [ ] 3.6 创建 `src/lib/components/pm/flowchart/NodeTypeManager.svelte` - 节点类型管理器
  - 创建自定义节点类型
  - 设置默认样式和图标
  - 类型列表管理

### Phase 4: 模块页面集成

- [ ] 4.1 在 `+page.svelte` 中新增 `flowchart` editorType 的处理逻辑
- [ ] 4.2 实现流程图数据的加载、保存、创建、删除
- [ ] 4.3 实现查看模式（只读）

### Phase 5: 参数清单关联（双向同步）

- [ ] 5.1 在参数清单表格中新增"关联节点"列
  - 显示格式：`参数 → 需求-流程图-节点名称`
  - 支持多节点关联显示
- [ ] 5.2 实现参数与流程图节点的关联查询
  - 反向索引：从参数ID查询关联的所有流程图节点
  - 缓存机制：避免频繁查询
- [ ] 5.3 实现双向同步机制
  - **流程图 → 参数清单**：节点参数变更时，更新参数清单中的 `flowchartRefs` 字段
  - **参数清单 → 流程图**：参数删除时，触发流程图数据清理
  - 同步 API：后端事务保证一致性
- [ ] 5.4 实现点击跳转功能（参数 → 流程图 → 节点）
  - 参数清单中的关联节点可点击
  - 跳转至对应流程图并高亮目标节点

### Phase 6: 验证与测试

- [ ] 6.1 验证流程图 CRUD 功能
- [ ] 6.2 验证节点拖拽、连线功能
- [ ] 6.3 验证参数关联功能
- [ ] 6.4 验证版本兼容性
- [ ] 6.5 运行 lint 和 type-check

## 验证命令

```bash
# 类型检查
npm run check

# 前端 lint
npm run lint:frontend

# 构建测试
npm run build
```

## 风险点

1. **SvelteFlow 版本兼容性**：当前 `@xyflow/svelte` 版本为 0.1.19，需确认 API 稳定性
2. **自定义节点渲染**：动态形状渲染（矩形、圆角、圆形、菱形、椭圆）需测试各浏览器兼容性
3. **双向同步复杂性**：参数关联的双向同步涉及多个模块的数据一致性，需仔细设计事务边界
4. **数据序列化**：Flowchart 数据存储在 JSON 字段中，自定义样式数据可能较大，需确保序列化/反序列化正确
5. **性能**：大量节点时的渲染性能，需考虑虚拟化或分页；自定义样式可能增加渲染开销

## Rollback 点

- 每个 Phase 完成后可独立回滚
- 主要回滚点：Phase 3 完成后（组件层面）、Phase 4 完成后（模块集成层面）
