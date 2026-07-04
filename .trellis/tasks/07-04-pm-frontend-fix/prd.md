# PM 工作台前端页面修复与 UI 优化

**父任务**: 07-04-open-webui-agent-integration
**日期**: 2026-07-04
**状态**: 规划中

---

## Goal

修复 PM 工作台中4个前端问题：产品架构页面加载卡住、流程图页面点击无响应、部分页面空白、表单UI丑陋。

## Current State

PM 工作台已有完整的前端页面结构（SvelteKit），但存在以下问题：

| 问题 | 现象 | 影响模块 |
|------|------|----------|
| 产品架构一直加载 | 页面显示 spinner 不消失 | product-architecture |
| 流程图点击无响应 | 点击条目无法进入编辑模式 | flowchart |
| 部分页面空白 | 进入模块后无内容显示 | 多个模块 |
| 表单UI丑 | 原生HTML控件，无视觉层次，样式不统一 | 所有表单模块 |

## Root Cause Analysis

### Bug 1: 产品架构一直加载

- **根因**: 产品架构 `editorType: 'mindmap'`，页面在 `isFormView || isMindmapView` 条件分支中渲染
- 当 `archView === 'mindmap'` 时，从 `filteredEntries` 提取 nodes 渲染 `PMMindMap`
- 如果后端 API 返回空数组或失败，页面只显示默认根节点或空白
- `product-architecture.ts` 中的 API 调用路径 `/projects/{id}/modules/product-architecture` 与后端统一 entries 路由不匹配
- **修复**: 确保前端使用统一的 `getEntries(token, projectId, 'product-architecture')` API；改善空状态和错误状态的展示

### Bug 2: 流程图点击无响应

- **根因**: 流程图 `editorType: 'flowchart'`，条目列表走 `{:else}` 分支（卡片列表）
- 点击卡片调用 `openEntryEditor(entry.id)`，但 `editingEntryId` 设置后，编辑器只在 `isFlowchartView && editingEntry` 条件下渲染 `PMFlowchartEditor`
- 如果 `@xyflow/svelte` 依赖未安装或版本不兼容，组件会报错
- 如果条目数据中 `flowchart` 字段缺失，`flowchartData` 为空对象导致渲染异常
- **修复**: 确保 `PMFlowchartEditor` 正确处理空数据；添加错误边界；验证 `@xyflow/svelte` 依赖

### Bug 3: 部分页面空白

- **根因**: API 调用失败被 catch 后 `entries=[]`，显示空状态而非错误提示
- 某些模块的 `loadRelatedEntries()` 静默失败（`console.warn` 但不展示给用户）
- **修复**: 改善错误处理，API 失败时显示明确的错误信息和重试按钮（当前已有 `loadError` 逻辑，需确保所有分支正确展示）

### Bug 4: 表单UI丑

- **根因**: 所有表单在一个 2600 行的巨型 `+page.svelte` 中
- 原生 HTML 控件 + Tailwind 简单样式，无组件库
- 创建表单和编辑表单样式不统一
- 大量重复的 class 字符串
- **修复**: 提取可复用表单组件，统一样式变量，改善视觉层次和分组

## Requirements

### R1: 产品架构页面修复

- 确保产品架构页面使用统一的 `getEntries` API（而非 `product-architecture.ts` 中的独立路径）
- 空状态：当没有条目时，显示引导用户创建第一个架构条目的提示
- 错误状态：API 失败时显示错误信息和重试按钮
- 思维导图视图：当条目有 nodes 数据时正确渲染，无数据时显示默认根节点

### R2: 流程图页面修复

- 确保流程图条目列表可点击进入编辑模式
- `PMFlowchartEditor` 正确处理空 flowchart 数据（`{ nodes: [], edges: [] }`）
- 添加错误边界：如果 `@xyflow/svelte` 加载失败，显示降级提示
- 确保流程图编辑器保存后数据正确回写

### R3: 空白页面修复

- 所有模块页面的 API 错误都应显示明确的错误信息（而非静默空白）
- `loadRelatedEntries` 失败时展示警告提示
- 确保所有模块类型的 `moduleConfig` 都有正确的配置

### R4: 表单 UI 优化

- 提取可复用表单组件：`PMFormField`、`PMFormSection`、`PMFormSelect`、`PMFormTextarea`、`PMFormToggle`
- 统一表单样式：一致的 padding、border、focus ring、label 样式
- 表单分组：相关字段用 section 分组，添加视觉层次
- 改善创建表单和编辑表单的一致性
- 保持 Tailwind 样式体系，不引入新组件库

## Dependencies

- 依赖 `07-04-pm-backend-api`（后端 API 必须先可用）

## Acceptance Criteria

- [ ] 产品架构页面能正常加载，空状态有引导提示，API 错误有重试按钮
- [ ] 流程图页面条目可点击进入编辑模式，空数据不崩溃
- [ ] 所有模块页面 API 失败时显示错误信息而非空白
- [ ] 表单使用可复用组件，视觉层次清晰，创建/编辑样式一致
- [ ] 不引入新的 npm 依赖
- [ ] 现有功能不受影响（回归测试）
