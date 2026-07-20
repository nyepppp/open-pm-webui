# Quickstart: 产品架构页面缺陷修复与交互重构

**Date**: 2026-07-10
**Feature**: specs/005-arch-bugfix-redesign

## Prerequisites

- Open WebUI dev server running on `localhost:5173`
- At least one PM project with existing architecture data (modules/functions/parameters)
- Valid user session (logged in)

## Validation Scenarios

### Scenario 1: Operation buttons work (FR-001, FR-002, FR-003, FR-009)

1. Navigate to `/pm/{projectId}/architecture`
2. Switch to "表格" tab
3. Click "编辑" button on any module row → verify edit modal opens with pre-filled data
4. Change the description and click "保存" → verify toast shows "更新成功" and table refreshes
5. Click "新增模块" button → verify modal opens, fill in name/key, click save → verify new module appears
6. Verify other module rows remain interactive (expand/collapse still works, no freeze)
7. Click "添加参数" (plus icon) on a feature row → verify parameter creation works

**Expected**: All buttons respond within 200ms, no freeze, no error toasts.

### Scenario 2: Mind map hierarchy (FR-007)

1. Navigate to `/pm/{projectId}/architecture`
2. Ensure "思维导图" tab is active
3. Verify root node shows project name (not "产品架构")
4. Verify module nodes appear as children of root
5. Verify function nodes appear as children of their module
6. Click on a module node → verify detail modal shows version info and description
7. Click on a function node → verify detail modal shows version info and description

**Expected**: Full 3-level hierarchy rendered, project name as root.

### Scenario 3: Batch parameter create (FR-004)

1. Navigate to `/pm/{projectId}/architecture`, "表格" tab
2. Expand a module, then expand one of its features
3. Click the "+" button on a feature row → verify batch form opens with 3 empty rows
4. Fill in 2 rows with valid data, leave 3rd row empty
5. Click "全部添加" → verify only 2 parameters are created (empty row skipped)
6. Test partial failure: create 3 rows, but make one have a duplicate KEY → verify none are created and error is shown

**Expected**: Batch form works, all-or-nothing on API failure, empty rows skipped.

### Scenario 4: Version info and demand relation display (FR-005, FR-006)

1. Navigate to `/pm/{projectId}/architecture`, "表格" tab
2. Verify "创建版本" column shows version strings (e.g., "1.0.0") not blank or "-"
3. Click on a demand relation tag in "关联需求" column → verify demand relation modal opens
4. Add a new demand relation → verify tag appears in table

**Expected**: Version column populated, demand relation modal accessible.

### Scenario 5: Version selector and AI button removed (FR-008)

1. Navigate to `/pm/{projectId}/architecture`
2. Verify page header only shows "产品架构" title and tab bar
3. Verify no "选择版本" button
4. Verify no "AI" button

**Expected**: Clean header with title + tabs only.

### Scenario 6: Data flow unified (FR-010)

1. Verify `ModuleTable.svelte` is no longer imported anywhere
2. Verify `src/lib/stores/pm/architectureStore.ts` architecture-specific code is removed
3. Verify only `src/lib/stores/pm/architecture.ts` is used for architecture data

**Expected**: Single data source, no duplicate stores.
