# PM工作台交互与UI修复

## Goal

修复 PM 工作台页面的 4 个关键问题，提升用户体验和页面性能。

## Background

用户在使用 PM 工作台（`/pm/:projectId` 及 `/pm/:projectId/architecture`）时遇到以下问题：

1. **导航切换无响应**：顶部导航栏点击后页面无反应
2. **架构页面卡顿**：`/pm/:projectId/architecture` 页面滚动和交互特别卡
3. **卡片样式不一致**：架构页面中模块卡片样式不统一，信息缺失（版本、创建时间、更新时间、溯源）
4. **"添加功能"按钮无响应**：点击 "+ 添加功能" 按钮无反应

## Confirmed Facts (from code inspection)

### Issue 1: 导航切换无响应
- **位置**: `src/routes/(app)/pm/[projectId]/+page.svelte`
- **根因**: 模块入口按钮使用 `<button onclick={() => goto(mod.href)}>`，但 `goto` 来自 `$app/navigation`。需要确认 SvelteKit 的 `goto` 是否被正确导入和使用。
- **相关代码**: 第 281-297 行，模块卡片按钮点击调用 `goto(mod.href)`

### Issue 2: 架构页面卡顿
- **位置**: `src/routes/(app)/pm/[projectId]/architecture/+page.svelte`
- **根因**: 
  - 页面使用 `h-[calc(100vh-200px)]` 固定高度，可能导致大量重渲染
  - `MindMapCanvas` 组件在 `{#key $aggregatedTree}` 下，每次数据变化都会重新创建
  - `ModuleFeatureTree` 和 `ModuleFeatureManager` 同时渲染大量 DOM 节点
  - `$effect` 监听 resize 事件但没有防抖
- **相关代码**: 第 34-39 行 (resize effect), 第 143-165 行 (MindMapCanvas)

### Issue 3: 卡片样式不一致 & 信息缺失
- **位置**: `src/lib/components/pm/architecture/ModuleCard.svelte`
- **根因**: 
  - `ModuleCard.svelte` 是卡片组件，但当前只显示：模块名称、功能数量、来源、参数数量、描述
  - **缺失信息**: 版本归属、创建时间、更新时间、溯源信息
  - 卡片样式可能与 `ModuleFeatureManager.svelte` 中的表格视图不一致
- **相关代码**: `ModuleCard.svelte` 第 56-107 行 (卡片内容)

### Issue 4: "添加功能"按钮无响应
- **位置**: `src/lib/components/pm/architecture/ModuleCard.svelte`
- **根因**: 
  - 按钮 `onclick={() => onAddFeature?.()}` 调用父组件传入的回调
  - 需要检查父组件 (`+page.svelte`) 中 `onAddFeature` 的实现
  - 当前 `+page.svelte` 中 `handleAddFeature` 函数存在，但需要确认是否被正确传递到 `ModuleCard`
- **相关代码**: `ModuleCard.svelte` 第 158-163 行, `+page.svelte` 第 53-61 行

## User Decisions

### 卡片信息展示 (Issue 3)
- **方案**: 采用紧凑方案（方案 A）
- **卡片显示**: 版本归属 + 更新时间 + 溯源入口
- **创建时间**: 放在 tooltip 或详情页，不直接显示在卡片上
- **目标**: 保持卡片紧凑且信息完整

### "添加功能"行为 (Issue 4)
- **方案**: 快捷添加（方案 B）
- **交互形式**: 弹窗（Modal）形式
- **弹窗内容**: 
  - 功能名称输入
  - 参数列表（可动态添加/删除参数）
  - 直接在当前模块下添加，无需选择模块
- **参数添加**: 支持在弹窗内直接新增参数
- **弹窗规范**: 使用项目已有的 `Modal.svelte` 组件（`src/lib/components/common/Modal.svelte`）
- **参数字段**: 参数名（必填）、类型（选填，默认 string）、描述（选填）、默认值（选填）

### 性能要求 (Issue 2)
- **数据规模**: 50-100 个模块
- **性能目标**: 
  - 滚动帧率 > 30fps
  - 页面加载时间 < 2s
  - 交互响应时间 < 100ms
- **优化策略**: 虚拟滚动、懒加载、防抖、减少重渲染

### 版本信息来源 (Issue 3)
- **来源**: 项目版本信息（`selectedVersion` from architecture page）
- **显示**: 当前选中的版本号，如 `v1.2.3`

## Requirements

### R1: 修复导航切换无响应
- 确保 PM 工作台页面模块入口点击后能正确跳转
- 修复 `goto` 导航逻辑

### R2: 优化架构页面性能
- 减少不必要的重渲染
- 优化 MindMapCanvas 的渲染策略
- 添加 resize 防抖
- 优化大数据量下的滚动性能（50-100 模块）
- 目标：滚动帧率 > 30fps，页面加载 < 2s

### R3: 统一卡片样式并补充信息
- 统一 `ModuleCard.svelte` 的卡片样式
- 卡片显示：版本归属（来自项目版本信息）、更新时间、溯源入口
- 创建时间放在 tooltip 或详情页
- 保持卡片紧凑

### R4: 修复"添加功能"按钮并优化交互
- 确保按钮点击能正确触发添加功能逻辑
- 实现弹窗形式的添加功能界面
- 弹窗内支持：功能名称输入 + 参数动态添加/删除
- 直接在当前模块下添加，无需选择模块
- 使用项目已有的 `Modal.svelte` 组件
- 参数字段：名称（必填）、类型（选填）、描述（选填）、默认值（选填）

## Acceptance Criteria

- [ ] 点击 PM 工作台模块入口能正确跳转到对应页面
- [ ] 架构页面滚动流畅，50-100 模块下帧率 > 30fps
- [ ] 模块卡片样式统一，显示版本归属（来自项目版本信息）、更新时间、溯源入口
- [ ] 点击 "+ 添加功能" 按钮弹出功能添加弹窗，支持参数管理
- [ ] 弹窗内可直接添加参数，提交后在当前模块下创建功能
- [ ] 弹窗使用项目统一的 Modal 组件

## Out of Scope

- 后端 API 修改（假设 API 已正确返回数据）
- 新增页面或路由
- 架构设计层面的重构（仅做修复和优化）
- 溯源详情页开发（仅添加入口）

## Open Questions

无剩余待确认问题。
