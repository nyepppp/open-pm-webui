# Implementation Plan: 架构可视化优化

## Phase 1: MindMap 组件开发

### 1.1 安装依赖
- [ ] 安装 d3: `npm install d3 @types/d3`

### 1.2 创建 MindMapCanvas 组件
- [ ] 创建 `src/lib/components/pm/mindmap/MindMapCanvas.svelte`
- [ ] 实现树形布局算法（d3-hierarchy）
- [ ] 实现 SVG 渲染（节点 + 连线）
- [ ] 实现交互（点击、缩放、拖拽）

### 1.3 数据转换器更新
- [ ] 更新 `excalidrawDataConverter.ts`
- [ ] 添加 `treeToMindMap` 函数
- [ ] 保持向后兼容

### 1.4 替换 Excalidraw
- [ ] 修改 `+page.svelte`
- [ ] 替换 `<ExcalidrawCanvas>` 为 `<MindMapCanvas>`
- [ ] 更新数据传递

## Phase 2: 模块卡片布局

### 2.1 创建 ModuleCard 组件
- [ ] 创建 `src/lib/components/pm/architecture/ModuleCard.svelte`
- [ ] 实现卡片样式（圆角、阴影、hover）
- [ ] 实现展开/收起功能

### 2.2 创建 FeatureCard 组件
- [ ] 创建 `src/lib/components/pm/architecture/FeatureCard.svelte`
- [ ] 实现内嵌卡片样式
- [ ] 实现参数表格展开

### 2.3 重构 ModuleFeatureManager
- [ ] 修改 `ModuleFeatureManager.svelte`
- [ ] 替换表格为卡片布局
- [ ] 保持现有功能（增删改查）

## Phase 3: 样式与交互优化

### 3.1 暗黑模式支持
- [ ] 添加 dark: 前缀样式
- [ ] 测试暗黑模式显示

### 3.2 响应式设计
- [ ] 移动端适配
- [ ] 卡片宽度自适应

### 3.3 动画效果
- [ ] 展开/收起动画
- [ ] 卡片 hover 动画

## Phase 4: 测试与验证

### 4.1 功能测试
- [ ] 思维导图正常显示
- [ ] 卡片布局正常显示
- [ ] 增删改查功能正常

### 4.2 兼容性测试
- [ ] 数据格式兼容
- [ ] 暗黑模式兼容
- [ ] 移动端兼容

## Rollback Plan
- 保留 Excalidraw 组件文件
- 保留原始表格布局代码
- 如需回滚，只需修改 `+page.svelte` 引用

## Validation Commands
```bash
# 构建测试
npm run build

# 类型检查
npx svelte-check

# 启动开发服务器测试
npm run dev
```
