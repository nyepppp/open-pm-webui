# 修复产品架构页面问题 - 技术设计

## 变更概述

本次修复涉及5个独立但相关的问题，分布在4个文件中。每个修复都是模块化的，可以独立验证。

## 文件变更计划

### 1. `src/routes/(app)/pm/[projectId]/+page.svelte`
**问题**: 工作台分页不工作
**修复**: 移除 `recentItems = sorted.slice(0, 20)` 中的 `.slice(0, 20)` 限制
**行号**: 第161行
**风险**: 低 - 仅移除限制，不影响其他逻辑

### 2. `src/routes/(app)/pm/[projectId]/architecture/+page.svelte`
**问题**: 页面卡顿 + 按钮不可点击
**修复**:
- 添加 `key` 属性控制 Excalidraw 重新渲染时机
- 优化 tab 切换，使用 `{#key}` 包裹内容
- 检查并修复可能的 z-index 问题
**风险**: 中 - 涉及React组件嵌入Svelte

### 3. `src/lib/utils/excalidrawDataConverter.ts`
**问题**: 思维导图布局混乱
**修复**: 重新实现 `treeToExcalidraw` 的布局算法
- 使用分层树形布局（Layered Tree Layout）
- 计算每个模块的水平位置：`centerX - (totalWidth / 2) + (index * spacing)`
- 计算功能的垂直位置：`moduleY + MODULE_HEIGHT + padding + (index * spacing)`
- 确保箭头连接点正确
**风险**: 中 - 需要测试不同数据量的情况

### 4. `src/lib/components/pm/ModuleFeatureManager.svelte`
**问题**: 布局应为表格而非卡片
**修复**:
- 将模块列表改为 `<table>` 布局
- 表头：模块名称 | 来源 | 功能数量 | 操作
- 展开后显示功能子表格
- 功能表格：功能名称 | 来源 | 参数数量 | 操作
- 操作按钮统一使用 `text-sm` 尺寸
**风险**: 低 - 主要是UI结构调整

## 依赖关系

```
修复1 (分页) ── 独立
修复2 (性能) ── 依赖修复3完成（布局正确后性能测试才有意义）
修复3 (思维导图) ── 独立
修复4 (表格布局) ── 独立
```

## 回滚策略

每个修复都是小范围修改，可以通过 git revert 单独回滚。

## 测试计划

1. **分页测试**: 创建超过20条记录，验证分页控件显示
2. **性能测试**: 使用 Chrome DevTools Performance 面板记录加载时间
3. **按钮测试**: 手动点击所有按钮验证响应
4. **思维导图测试**: 验证不同模块/功能数量的布局
5. **表格测试**: 验证响应式布局和深色模式

## 兼容性

- 保持现有 API 不变
- 保持现有数据结构不变
- 仅修改前端展示逻辑
