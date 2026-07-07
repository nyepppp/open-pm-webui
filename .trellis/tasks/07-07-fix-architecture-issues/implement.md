# 修复产品架构页面问题 - 执行计划

## 执行顺序

### 阶段1: 快速修复（预计30分钟）
1. **修复工作台分页** - `+page.svelte` 移除20条限制
2. **修复表格布局** - `ModuleFeatureManager.svelte` 改为表格

### 阶段2: 性能优化（预计1小时）
3. **修复思维导图布局** - `excalidrawDataConverter.ts` 重新实现布局
4. **修复页面性能** - `architecture/+page.svelte` 优化渲染

### 阶段3: 验证（预计30分钟）
5. 运行 lint 检查
6. 手动测试所有修复点

## 详细步骤

### 步骤1: 修复工作台分页
```bash
# 文件: src/routes/(app)/pm/[projectId]/+page.svelte
# 修改: 第161行
```
- [ ] 找到 `recentItems = sorted.slice(0, 20);`
- [ ] 改为 `recentItems = sorted;`
- [ ] 验证分页控件在数据超过20条时显示

### 步骤2: 修复功能列表表格布局
```bash
# 文件: src/lib/components/pm/ModuleFeatureManager.svelte
```
- [ ] 将模块列表改为 `<table>` 结构
- [ ] 表头：模块名称 | 来源 | 功能数量 | 操作
- [ ] 功能列表改为子表格
- [ ] 统一操作按钮样式

### 步骤3: 修复思维导图布局算法
```bash
# 文件: src/lib/utils/excalidrawDataConverter.ts
# 函数: treeToExcalidraw
```
- [ ] 重新设计布局算法
- [ ] 计算模块水平位置
- [ ] 计算功能垂直位置
- [ ] 确保箭头连接正确

### 步骤4: 修复架构页面性能
```bash
# 文件: src/routes/(app)/pm/[projectId]/architecture/+page.svelte
```
- [ ] 添加 `{#key}` 控制 Excalidraw 渲染
- [ ] 检查 z-index 问题
- [ ] 优化 tab 切换

## 验证清单

- [ ] `npm run lint` 通过
- [ ] 工作台分页正确工作
- [ ] 功能列表显示为表格
- [ ] 思维导图布局正确
- [ ] 页面无卡顿
- [ ] 所有按钮可点击
- [ ] 深色模式正常
- [ ] 响应式布局正常

## 回滚命令

```bash
# 如果需要回滚所有修改
git checkout -- src/routes/(app)/pm/[projectId]/+page.svelte
git checkout -- src/routes/(app)/pm/[projectId]/architecture/+page.svelte
git checkout -- src/lib/utils/excalidrawDataConverter.ts
git checkout -- src/lib/components/pm/ModuleFeatureManager.svelte
```
