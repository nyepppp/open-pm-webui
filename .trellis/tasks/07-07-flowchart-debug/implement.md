# 执行计划：流程图功能问题排查与修复

## 执行顺序

### Phase 1：诊断与信息收集
- [ ] 1.1 读取流程图页面入口文件，理解组件结构
- [ ] 1.2 读取 `excalidrawDataConverter.ts` 分析 LSP 错误
- [ ] 1.3 读取 `flowchart.ts` API 文件分析 LSP 错误
- [ ] 1.4 检查 Excalidraw 容器组件的 props 和渲染逻辑

### Phase 2：修复形状渲染问题
- [ ] 2.1 定位形状创建逻辑
- [ ] 2.2 修复 `excalidrawDataConverter.ts` 的语法错误
- [ ] 2.3 验证形状类型枚举映射
- [ ] 2.4 测试各形状渲染效果

### Phase 3：修复 Excalidraw 集成
- [ ] 3.1 检查右侧面板的渲染方式
- [ ] 3.2 调整面板层级或改用 Excalidraw 扩展 API
- [ ] 3.3 验证面板与画布的交互

### Phase 4：修复实体绑定按钮
- [ ] 4.1 修复 `flowchart.ts` 的类型错误
- [ ] 4.2 检查按钮点击事件绑定
- [ ] 4.3 验证 API 调用和响应处理
- [ ] 4.4 测试各实体类型的查询功能

### Phase 5：验证与收尾
- [ ] 5.1 运行类型检查确保无新增错误
- [ ] 5.2 运行相关测试
- [ ] 5.3 更新任务状态

## 验证命令

```bash
# 类型检查
npm run type-check

# 相关测试
npm test -- flowchart
```

## 回滚点

- 每个 Phase 完成后为独立回滚点
- 关键文件变更前备份原始状态
