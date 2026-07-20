# Tasks: 产品架构页面缺陷修复与交互重构

**Input**: Design documents from `/specs/005-arch-bugfix-redesign/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested — test tasks omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Clean Up Dead Code)

**Purpose**: Remove obsolete components and stores that cause data conflicts

- [x] T001 [US1] Delete `src/lib/components/pm/architecture/ModuleTable.svelte` — replaced by ArchitectureTable per FR-010
- [x] T002 [P] [US1] Delete `src/lib/components/pm/architecture/ModuleCard.svelte` — only referenced by deleted ModuleTable/ModuleFeatureManager
- [x] T003 [P] [US1] Delete `src/lib/components/pm/architecture/ModuleFeatureManager.svelte` — only referenced by deleted ModuleTable
- [x] T004 [P] [US1] Delete `src/lib/components/pm/architecture/ModuleFeatureTree.svelte` — only referenced by deleted ModuleFeatureManager
- [x] T005 [US1] Delete dead route `src/routes/pm/architecture/+page.svelte` — orphan route using old store
- [x] T006 [US1] Remove architecture-specific exports from `src/lib/stores/pm/architectureStore.ts` — delete `architectureHierarchy`, `convertToArchModules`, `aggregatedTree`, `architectureModules` and related types; keep `parameterEntries`, `archEntries`, `loadData` for other modules that may use them
- [x] T007 [US1] Verify no remaining imports of deleted files across the codebase — fix any broken imports

**Checkpoint**: Dead code removed, no broken imports, project compiles cleanly

---

## Phase 2: Foundational (Unify Data Flow)

**Purpose**: Fix the core data flow so +page.svelte and ArchitectureTable use the same store

**⚠️ CRITICAL**: This phase fixes the root cause of most bugs. No user story work is meaningful until this is done.

- [x] T008 [US1] Rewrite `src/routes/(app)/pm/[projectId]/architecture/+page.svelte` to use old `architectureStore` from `src/lib/stores/pm/architecture.ts` — replace `architectureHierarchy` subscription with `architectureStore.loadAll()`, use `$activeModules`/`$activeFunctions`/`$activeParameters`; remove `handleTableEdit`/`handleTableDelete`/`handleTableAdd` callbacks that used new-system `createEntry`/`updateEntry`/`deleteEntry`; remove version selector and AI button
- [x] T009 [US1] Rewrite `src/lib/components/pm/architecture/ArchitectureTable.svelte` to use old `architectureStore` directly — remove props-based data flow (`modules`, `onEdit`, `onDelete`, `onAdd`); subscribe to `$activeModules`/`$activeFunctions`/`$activeParameters` from old store; call `architectureStore.updateModule()`/`createModule()`/`softDeleteModule()` etc. directly instead of emitting events to parent; fix `createVersion` field name mapping (use `create_version` not `createVersion`); ensure `demand_relation` click opens `DemandRelationModal`

**Checkpoint**: Data flows through single store, operations call correct API endpoints

---

## Phase 3: User Story 1 — Fix Operation Failures & Data Updates (Priority: P1) 🎯 MVP

**Goal**: All table operation buttons (edit, add, delete, copy) work correctly without freezing or errors

**Independent Test**: Click each operation button in table view — verify modal opens, data saves, table refreshes, no freeze

### Implementation for User Story 1

- [x] T010 [US1] Fix edit flow in `src/lib/components/pm/architecture/ArchitectureTable.svelte` — ensure `handleEdit` opens `ModuleForm` with correct entity data; `handleEditSubmit` calls `architectureStore.updateModule()`/`updateFunction()`/`updateParameter()` with real backend IDs (not synthetic IDs); verify success toast and data refresh
- [x] T011 [US1] Fix "新增模块" flow — ensure `handleAddModule` in ArchitectureTable calls `architectureStore.createModule()` and new module appears without freezing other rows; investigate and fix any reactive loop caused by store update
- [x] T012 [US1] Fix "添加参数" flow — ensure `handleAddParameter` in ArchitectureTable calls `architectureStore.createParameter()` with correct `function_id` and parameter is created successfully
- [x] T013 [US1] Fix "新增下级" (add child) flow — module→function and function→parameter child creation works via `architectureStore.createFunction()`/`createParameter()`
- [x] T014 [US1] Fix delete flow — ensure `handleDeleteConfirm` calls `architectureStore.softDeleteModule()`/`softDeleteFunction()`/`softDeleteParameter()` and table refreshes
- [x] T015 [US1] Fix copy flow — ensure `handleCopyConfirm` calls `architectureStore.copyModule()`/`copyFunction()`/`copyParameter()` and new entry appears
- [x] T016 [US1] Fix update failure toast — ensure all store methods catch errors and show user-friendly error toasts; verify success toast on completion

**Checkpoint**: All CRUD operations work in table view without errors or freezing

---

## Phase 4: User Story 2 — Fix Mind Map Hierarchy (Priority: P1)

**Goal**: Mind map shows project→module→function 3-level hierarchy with correct root node

**Independent Test**: Switch to mind map tab — verify root shows project name, modules and functions appear as children, clicking nodes shows details

### Implementation for User Story 2

- [ ] T017 [US2] Add `projectName` prop to `src/lib/components/pm/architecture/MindMapView.svelte` — use it as root node label instead of hardcoded "产品架构"; pass from `+page.svelte` which calls `getProject(token, projectId)` to fetch project name
- [ ] T018 [US2] Fix MindMapView data source — currently subscribes to old store `$activeModules`/`$activeFunctions`/`$activeParameters` which is correct after Phase 2; verify `transformToTreeData()` correctly builds module→function hierarchy using old store data; ensure parameter nodes are NOT shown (only module→function per spec)
- [ ] T019 [US2] Fix NodeDetailModal content in `src/lib/components/pm/architecture/NodeDetailModal.svelte` — ensure clicked node shows version info (`create_version`) and description; fix data mapping from old store model (Module/Function have `create_version`, `version_record`, `demand_relation` fields)
- [ ] T020 [US2] Add empty state for mind map — when no modules exist, show "暂无架构数据" placeholder instead of blank canvas

**Checkpoint**: Mind map renders full hierarchy with project name root, node details show version+description

---

## Phase 5: User Story 3 — Batch Parameter Create Form (Priority: P2)

**Goal**: Parameter creation uses batch form with multiple rows, all-or-nothing submit

**Independent Test**: Click "添加参数" on a feature row — verify batch form opens with 3 rows, can add/remove rows, submit creates all or none

### Implementation for User Story 3

- [ ] T021 [US3] Create `src/lib/components/pm/architecture/BatchParameterForm.svelte` — batch form with default 3 rows; each row has: name, key, data_type (select), required (checkbox); "添加更多行" button adds empty row; "删除行" button removes specific row; form validates at least one complete row; all-or-nothing submit strategy
- [ ] T022 [US3] Integrate BatchParameterForm into ArchitectureTable — replace single-parameter `handleAddParameter` flow: clicking "+" on a feature row opens BatchParameterForm instead of ModuleForm; on submit, call `architectureStore.createParameter()` sequentially for each row; if any fails, delete already-created entries and show error
- [ ] T023 [US3] Add empty row skip logic — rows with empty name are silently skipped on submit; if ALL rows are empty, show "请至少填写一行数据" error and disable submit button

**Checkpoint**: Batch parameter creation works, all-or-nothing on failure, empty rows skipped

---

## Phase 6: User Story 4 — Fix Version Info & Demand Relation Display (Priority: P2)

**Goal**: "创建版本" column shows version strings, demand relation interaction works correctly

**Independent Test**: Verify version column populated, demand relation tags clickable and open modal

### Implementation for User Story 4

- [ ] T024 [P] [US4] Fix "创建版本" column display in `src/lib/components/pm/architecture/ArchitectureTable.svelte` — ensure `create_version` field from old store model (Module/Function/Parameter) is rendered; default to "1.0.0" if field is missing; the old store's Module model has `create_version: string` on BaseEntity
- [ ] T025 [US4] Fix demand relation interaction in ArchitectureTable — ensure clicking a DemandRelationTag or the demand relation cell area opens `DemandRelationModal`; currently the tag dispatches `click-tag` event but handler may be broken; wire up to open modal with correct entity type and ID
- [ ] T026 [US4] Fix demand relation in ModuleForm — ensure `DemandRelationTag` and `DemandRelationModal` inside `ModuleForm.svelte` work correctly with old store's `demand_relation` field mapping

**Checkpoint**: Version column shows data, demand relation modal opens and works

---

## Phase 7: User Story 5 — Remove Unnecessary Buttons (Priority: P3)

**Goal**: Remove "选择版本" and "AI" buttons from page header

**Independent Test**: Page header shows only title + tab bar

### Implementation for User Story 5

- [ ] T027 [US5] Remove version selector and AI button from `src/routes/(app)/pm/[projectId]/architecture/+page.svelte` — delete `showVersionSelector` state, `selectedVersion` state, version selector button HTML, AI button HTML, and `<PMVersionSelector>` component instance; keep `PMVersionSelector.svelte` file in codebase for future use

**Checkpoint**: Clean header with title + tabs only

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and cleanup

- [ ] T028 Verify all deleted files have no remaining imports — search codebase for `ModuleTable`, `ModuleCard`, `ModuleFeatureManager`, `ModuleFeatureTree` references
- [ ] T029 [P] Remove unused imports in modified files — clean up `architectureStore.ts` imports in `+page.svelte`, `ArchitectureTable.svelte`
- [ ] T030 Run quickstart.md validation — execute all 6 validation scenarios from `specs/005-arch-bugfix-redesign/quickstart.md`
- [ ] T031 Commit all changes with descriptive message

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2 — operations must use correct store first
- **Phase 4 (US2)**: Depends on Phase 2 — mind map must use correct store first
- **Phase 5 (US3)**: Depends on Phase 2 — batch form uses store methods
- **Phase 6 (US4)**: Depends on Phase 2 — version/demand fix needs correct store
- **Phase 7 (US5)**: Can run in parallel with Phase 3-6 (different file areas)
- **Phase 8 (Polish)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 — No dependencies on other stories
- **US2 (P1)**: Depends on Phase 2 — No dependencies on US1
- **US3 (P2)**: Depends on Phase 2 — No dependencies on US1/US2
- **US4 (P2)**: Depends on Phase 2 — No dependencies on US1/US2/US3
- **US5 (P3)**: No dependencies — can run any time

### Parallel Opportunities

- Phase 1 tasks T001-T004 can all run in parallel (different files)
- US1 and US2 can run in parallel after Phase 2 (different component files)
- US3, US4, US5 can run in parallel after Phase 2
- T024 and T025 in US4 can run in parallel (different concerns)

---

## Parallel Example: Phase 1

```bash
# Launch all Phase 1 deletes together:
Task: "Delete ModuleTable.svelte"
Task: "Delete ModuleCard.svelte"
Task: "Delete ModuleFeatureManager.svelte"
Task: "Delete ModuleFeatureTree.svelte"
```

## Parallel Example: After Phase 2

```bash
# Launch US1, US2, US4 in parallel:
Task: "Fix edit flow in ArchitectureTable (US1)"
Task: "Fix MindMapView hierarchy (US2)"
Task: "Fix version column display (US4)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Delete dead code
2. Complete Phase 2: Unify data flow
3. Complete Phase 3: Fix operations (US1)
4. **STOP and VALIDATE**: All CRUD operations work
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Data flow fixed
2. Add US1 → Operations work (MVP!)
3. Add US2 → Mind map fixed
4. Add US3 → Batch create
5. Add US4 → Version info and demand relations
6. Add US5 → Remove buttons
7. Polish → Final validation

---

## Notes

- The root cause of most bugs is the dual store/API conflict — fixing this in Phase 2 unblocks everything
- After Phase 2, `ArchitectureTable.svelte` uses old store directly, so all operation handlers naturally work with correct backend IDs
- `MindMapView.svelte` already subscribes to old store data — after Phase 2 removes the competing new store, it will automatically get correct data
- The old store's `architecture.ts` API uses dedicated endpoints (`/api/pm/modules`, `/api/pm/functions`, `/api/pm/parameters`) which are more reliable than the generic entry endpoints
- `create_version` field exists on the old model's `BaseEntity` — it should populate correctly once we use the old store
