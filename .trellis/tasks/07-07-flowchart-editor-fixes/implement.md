# 流程图编辑器缺陷修复 - 实施计划

## 实施步骤

### Phase 1: 节点形状修复（预计 1 小时）

- [ ] **1.1** 分析 Excalidraw 支持的形状类型
  - 检查 Excalidraw API 文档，确认支持的元素类型
  - 验证 rectangle, ellipse, diamond 等类型的实际支持情况

- [ ] **1.2** 修复 `excalidrawDataConverter.ts`
  - 修复 `flowchartToExcalidraw` 函数的形状映射
  - 修复 `excalidrawToFlowchart` 函数的形状还原
  - 确保自定义形状（如圆角矩形）正确处理

- [ ] **1.3** 验证形状创建
  - 测试不同节点类型的创建和显示
  - 验证形状切换功能

### Phase 2: 节点配置面板融合（预计 1.5 小时）

- [ ] **2.1** 修复 ExcalidrawCanvas 事件监听
  - 改进 `onPointerDown` 事件处理
  - 确保元素点击事件正确传递

- [ ] **2.2** 修复 `PMFlowchartEditor.svelte`
  - 完善 `handleElementClick` 函数
  - 修复 `updateNodeData` 函数，支持形状/颜色更新
  - 确保配置面板正确显示和关闭

- [ ] **2.3** 修复 `NodeConfigPanel.svelte`
  - 验证形状选择后的同步逻辑
  - 测试参数绑定功能

### Phase 3: 溯源绑定修复（预计 1 小时）

- [ ] **3.1** 检查 TraceabilitySidebar props 传递
  - 验证 `nodeData` 和 `traceability` 数据流
  - 修复可能的类型不匹配问题

- [ ] **3.2** 检查 EntityBindingPanel 功能
  - 验证实体搜索和选择
  - 修复绑定保存逻辑

- [ ] **3.3** 验证溯源数据保存
  - 测试绑定 → 保存 → 重新加载流程

### Phase 4: 导出功能实现（预计 1.5 小时）

- [ ] **4.1** 完善 PNG 导出
  - 利用 Excalidraw 原生 `exportToBlob` API
  - 添加文件名和格式选项

- [ ] **4.2** 实现 SVG 导出
  - 使用 Excalidraw `exportToSvg` API
  - 处理 SVG 下载

- [ ] **4.3** 实现 Markdown 导出
  - 将 FlowchartData 转换为 Markdown 文本描述
  - 支持下载 .md 文件

- [ ] **4.4** 实现 drawio 导出
  - 将 FlowchartData 转换为 draw.io XML 格式
  - 支持下载 .drawio 文件

### Phase 5: 工作台分页和架构页面优化（预计 1 小时）

- [ ] **5.1** 工作台分页
  - 在模块列表组件中添加分页逻辑
  - 每页显示 20 条

- [ ] **5.2** 架构页面性能优化
  - 优化思维导图渲染
  - 改进模块结构展示

### Phase 6: 测试验证（预计 1 小时）

- [ ] **6.1** 功能测试
  - 节点形状创建和切换
  - 配置面板弹出和修改
  - 溯源绑定流程
  - 导出功能

- [ ] **6.2** 集成测试
  - 完整流程：创建 → 配置 → 绑定 → 导出

- [ ] **6.3** 回归测试
  - 确保现有功能不受影响

## 验证命令

```bash
# 类型检查
npm run check

# 构建测试
npm run build

# 开发服务器测试
npm run dev
```

## 风险点

| 风险 | 应对措施 |
|------|---------|
| Excalidraw API 限制 | 查阅官方文档，使用替代方案 |
| 数据转换丢失信息 | 添加单元测试验证转换完整性 |
| 导出格式兼容性 | 验证生成的文件可被目标软件打开 |

## 回滚点

- Phase 1 完成后：验证形状功能
- Phase 2 完成后：验证配置面板
- Phase 3 完成后：验证溯源绑定
- Phase 4 完成后：验证导出功能
- 全部完成后：最终回归测试
