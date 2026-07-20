# PM Bug Fix Plan

## Bug Analysis & Fixes

### Bug #1: 产品架构页面点击报错
**File**: `src/routes/pm/architecture/+page.svelte`
**Issue**: Imports `architectureStore` from `$lib/stores/pm/architecture` but uses `$activeModules` etc which don't exist in the store
**Fix**: Update imports to use correct store exports

### Bug #2: 实体类型加载失败 (flowchart)
**File**: `src/lib/components/pm/flowchart/EntityBindingPanel.svelte`
**Issue**: `getEntries` API call may fail with 404 when module has no data
**Fix**: Add better error handling and empty state

### Bug #3: 选择项目没有和PM工作台打通
**File**: `src/lib/components/pm/PMDataSelector.svelte`
**Issue**: After selecting project, doesn't update `projectStore`
**Fix**: Import and call `setCurrentProject` after selection

### Bug #4: integration-menu-button 点击无响应
**File**: `src/lib/components/chat/MessageInput.svelte`
**Issue**: Button has `preventDefault` but no actual toggle logic for IntegrationsMenu
**Fix**: The IntegrationsMenu component should handle its own toggle

### Bug #5: 项目选择后数据读取不了
**File**: `src/routes/(app)/pm/[projectId]/+layout.svelte`
**Issue**: `loadProject` uses `$effect` which may run before mount
**Fix**: Ensure proper initialization sequence

### Bug #6: 工作流创建不了 + 布局错乱
**File**: Multiple workflow files
**Issue**: Layout issues and possibly missing workflow API endpoints
**Fix**: Check workflow routes and fix layout

### Bug #7: 产品架构表格展示不了
**File**: `src/routes/(app)/pm/[projectId]/architecture/+page.svelte`
**Issue**: Page imports from wrong store or missing data loading
**Fix**: Correct imports and add data loading

### Bug #8: 侧边栏点击无响应
**File**: Sidebar components
**Issue**: Event handlers may be blocked or routes not configured
**Fix**: Check event propagation and routing

### Bug #9: 不能选择工作流
**File**: `src/lib/components/chat/WorkflowSelector.svelte`
**Issue**: Component may not receive correct props or events
**Fix**: Verify component integration

### Bug #10: 参数/实体按钮加载失败
**File**: `src/lib/components/pm/flowchart/EntityBindingPanel.svelte`
**Issue**: Same as Bug #2 - API error handling
**Fix**: Same fix as Bug #2

## Implementation Order

1. Fix Bug #3 (Project selection - foundational)
2. Fix Bug #5 (Project data loading)
3. Fix Bug #1 & #7 (Architecture page)
4. Fix Bug #2 & #10 (Entity loading)
5. Fix Bug #4 (Integration menu)
6. Fix Bug #8 (Sidebar)
7. Fix Bug #9 (Workflow selector)
8. Fix Bug #6 (Workflow creation)
