# Excalidraw 集成实施计划

## 实施步骤

### Phase 1: 环境准备（预计 30 分钟）✅ 已完成

- [x] **1.1** 安装依赖
  ```bash
  npm install react react-dom @excalidraw/excalidraw
  ```

- [x] **1.2** 验证安装
  - 检查 `package.json` 确认依赖已添加
  - 运行 `npm run check` 确认无类型错误

- [x] **1.3** 备份现有文件
  ```bash
  cp src/lib/components/pm/PMFlowchartEditor.svelte src/lib/components/pm/PMFlowchartEditor.xyflow.svelte
  cp src/lib/components/pm/flowchart/DynamicNode.svelte src/lib/components/pm/flowchart/DynamicNode.xyflow.svelte
  cp src/lib/components/pm/flowchart/CustomEdge.svelte src/lib/components/pm/flowchart/CustomEdge.xyflow.svelte
  ```

### Phase 2: 核心组件开发（预计 2-3 小时）✅ 已完成

- [x] **2.1** 创建 `ExcalidrawCanvas.svelte`（Svelte-React 桥接）
  - 文件：`src/lib/components/pm/excalidraw/ExcalidrawCanvas.svelte`
  - 使用 `react-dom/client` 创建 React 根
  - 暴露 `excalidrawAPI` 供父组件调用
  - 处理生命周期（mount/unmount）

- [x] **2.2** 创建 `ExcalidrawDataConverter.ts`（数据转换层）
  - 文件：`src/lib/utils/excalidrawDataConverter.ts`
  - 实现 `FlowchartData → Excalidraw JSON` 转换
  - 实现 `Excalidraw JSON → FlowchartData` 转换
  - 单元测试

- [x] **2.3** 重写 `PMFlowchartEditor.svelte`
  - 替换 `@xyflow/svelte` 为 Excalidraw
  - 集成 `ExcalidrawCanvas` 组件
  - 集成数据转换层
  - 保留节点配置面板
  - 保留可追溯性侧边栏

### Phase 3: 功能适配（预计 2-3 小时）✅ 已完成

- [x] **3.1** 节点类型映射
  - 实现 6 种节点类型的 Excalidraw 形状渲染
  - 配置节点颜色（与现有样式一致）

- [x] **3.2** 节点配置面板适配
  - 点击 Excalidraw 元素时弹出配置面板
  - 支持编辑标签、描述、参数绑定

- [x] **3.3** 可追溯性适配
  - 在 Excalidraw 元素中存储可追溯性数据
  - 集成可追溯性侧边栏

- [x] **3.4** 导出功能适配
  - 支持 PNG/SVG/JSON 导出
  - 保留现有 `exportFlowchart.ts` 兼容

### Phase 4: 测试验证（预计 1-2 小时）✅ 已完成

- [x] **4.1** 功能测试
  - 画布正常渲染
  - 自由绘制形状、箭头、文本
  - 节点配置面板正常工作
  - 可追溯性侧边栏正常工作
  - 导出功能正常

- [x] **4.2** 数据兼容性测试
  - 现有 `FlowchartData` 数据能正常加载
  - 新保存的数据格式正确
  - 向后兼容

- [x] **4.3** 性能测试
  - 检查 bundle 体积变化
  - 检查渲染性能

### Phase 5: 清理与交付（预计 30 分钟）✅ 已完成

- [x] **5.1** 清理旧代码
  - 删除 `@xyflow/svelte` 相关备份文件（确认新实现稳定后）
  - 删除 `PMFlowchartEditor.xyflow.svelte`
  - 删除 `DynamicNode.xyflow.svelte`
  - 删除 `CustomEdge.xyflow.svelte`

- [x] **5.2** 修复构建问题
  - 修复 Excalidraw CSS 导入路径：`@excalidraw/excalidraw/dist/prod/index.css` → `@excalidraw/excalidraw/index.css`

- [x] **5.3** 最终验证
  - 运行 `npm run check` ✅ （无 Excalidraw 相关错误）
  - 运行 `npm run build` ✅ （构建成功）

## 验证命令

```bash
# 类型检查
npm run check

# 代码检查
npm run lint

# 构建测试
npm run build

# 开发服务器测试
npm run dev
```

## 风险点与回滚

| 风险 | 应对措施 |
|------|---------|
| React 与 Svelte 5 不兼容 | 使用 React 18（而非 19），测试兼容性 |
| Excalidraw 渲染性能问题 | 使用 `viewModeEnabled` 优化，必要时降级 |
| 数据转换丢失信息 | 保留原始 `FlowchartData`，转换失败时回退 |
| 用户不习惯新交互 | 保留旧版本作为备选，A/B 测试 |

## 回滚方案

如需回滚：
1. 恢复备份文件：`PMFlowchartEditor.xyflow.svelte` → `PMFlowchartEditor.svelte`
2. 恢复 `DynamicNode.svelte` 和 `CustomEdge.svelte`
3. 卸载 Excalidraw 依赖：`npm uninstall react react-dom @excalidraw/excalidraw`

## 文件清单

### 新增文件
- `src/lib/components/pm/excalidraw/ExcalidrawCanvas.svelte`
- `src/lib/utils/excalidrawDataConverter.ts`
- `src/lib/utils/excalidrawDataConverter.test.ts`

### 修改文件
- `src/lib/components/pm/PMFlowchartEditor.svelte`（重写）
- `package.json`（添加依赖）

### 删除文件（备份文件已清理）
- ~~`src/lib/components/pm/PMFlowchartEditor.xyflow.svelte`~~
- ~~`src/lib/components/pm/flowchart/DynamicNode.xyflow.svelte`~~
- ~~`src/lib/components/pm/flowchart/CustomEdge.xyflow.svelte`~~

## 时间估算

| Phase | 预计时间 |
|-------|---------|
| Phase 1: 环境准备 | 30 分钟 |
| Phase 2: 核心组件 | 2-3 小时 |
| Phase 3: 功能适配 | 2-3 小时 |
| Phase 4: 测试验证 | 1-2 小时 |
| Phase 5: 清理交付 | 30 分钟 |
| **总计** | **6-9 小时** |
