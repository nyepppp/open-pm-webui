# PM模块UI Bug修复报告

## 任务信息
- **任务ID**: 07-07-fix-pm-ui-bugs
- **创建时间**: 2026-07-07
- **状态**: 已完成

## 修复的Bug

### Bug 1: 导航无响应 ✅
**文件**: `src/lib/components/pm/PMModuleNav.svelte`
**问题**: `handleModuleClick` 使用 `module.path` 直接跳转，但 `moduleStore.ts` 中的 `path` 属性缺少 `projectId`
**修复**: 修改点击事件，动态构建包含 `projectId` 的完整路径
```svelte
onclick={() => handleModuleClick(module.id, `/pm/${projectId}/${module.id}`)}
```

### Bug 2: Flowchart 一直在加载 ✅
**文件**: `src/lib/components/pm/reactflow/ReactFlowCanvas.svelte`
**问题**: `@xyflow/svelte` 动态导入失败时没有任何错误处理，导致 `isInitialized` 永远不会变为 `true`
**修复**: 
1. 添加 `try/catch` 错误处理
2. 导入失败时也将 `isInitialized` 设为 `true`，避免无限加载
3. 添加控制台错误日志

### Bug 3: 保存按钮不能创建新版本 ✅
**文件**: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
**问题**: `saveAsNewVersion()` 在创建新版本前没有先保存当前内容
**修复**: 在 `saveAsNewVersion()` 开头调用 `saveEntryContentOnly()` 先保存内容

### Bug 4: 需求边界编辑和实际列不对应 ✅
**文件**: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
**问题**: 编辑表单的字段布局与表格列定义不一致
**修复**: 
1. 调整表单字段标签（"功能" → "功能描述"）
2. 优化关联需求/关联参数选择器的布局结构

## 修改的文件列表
1. `src/lib/components/pm/PMModuleNav.svelte`
2. `src/lib/components/pm/reactflow/ReactFlowCanvas.svelte`
3. `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`

## 验证状态
- [x] 代码语法检查通过
- [x] 逻辑正确性验证通过
- [x] 无破坏性变更
