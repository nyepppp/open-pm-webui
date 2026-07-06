# 深度重构架构图模块

## TL;DR

> **目标**: 将 `architecture/+page.svelte` 从 505 行单体文件重构为模块化架构
>
> **核心策略**: 数据层提取 → 状态管理提取 → UI 组件化 → 性能优化 → 错误处理
>
> **预期结果**: +page.svelte 行数 < 200，加载时间缩短，新增骨架屏和错误重试
>
> **Estimated Effort**: Large
> **Parallel Execution**: YES - 5 waves
> **Critical Path**: Wave 1 → Wave 2 → Wave 3 → Wave 4 → Wave 5

---

## Context

### Original Request
用户要求"重构一下该模块"，期望深度重构优化。

### Current State Analysis
- `src/routes/(app)/pm/[projectId]/architecture/+page.svelte` — 505 行单体文件
- 混合了数据加载、状态管理、业务逻辑、UI 渲染
- 无骨架屏、无数据缓存、无错误重试
- Tab 切换、加载状态、错误处理等逻辑无法复用

### Research Findings
- 项目使用 Svelte 5 + Tailwind CSS
- 已有 `src/lib/stores/pm/` 目录存放 PM 相关 stores
- 已有 `src/lib/components/pm/` 目录存放 PM 组件
- API 层在 `src/lib/apis/pm/index.ts`

---

## Work Objectives

### Core Objective
将 architecture 页面重构为模块化、可维护、高性能的架构，同时保持所有现有功能。

### Concrete Deliverables
1. `src/lib/stores/pm/architectureStore.ts` — 数据加载和状态管理
2. `src/lib/services/architectureService.ts` — 业务逻辑
3. `src/lib/components/pm/architecture/ArchitectureTabBar.svelte`
4. `src/lib/components/pm/architecture/ArchitectureLoading.svelte`
5. `src/lib/components/pm/architecture/ArchitectureError.svelte`
6. `src/lib/components/pm/architecture/ArchitectureLayout.svelte`
7. 重构后的 `+page.svelte`（< 200 行）

### Definition of Done
- `+page.svelte` 行数 < 200
- 所有现有功能正常
- 新增骨架屏和错误重试
- TypeScript 类型完整
- 无编译错误

### Must Have
- 数据层提取
- 状态管理提取
- UI 组件化
- 骨架屏
- 错误重试

### Must NOT Have (Guardrails)
- 不改变现有 API 接口
- 不改变现有组件（PMMindMap、ModuleFeatureTree、ParameterTable）的接口
- 不引入新的依赖库
- 不改变用户交互流程

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES
- **Automated tests**: None
- **Framework**: bun test / vitest
- **Agent-Executed QA**: Playwright 验证页面加载、Tab 切换、数据展示

### QA Policy
Every task MUST include agent-executed QA scenarios.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation - Data Layer):
├── Task 1: Create architectureStore.ts (data loading, caching)
├── Task 2: Create architectureService.ts (business logic)
└── Task 3: Extract data transformation functions

Wave 2 (State Management):
├── Task 4: Create reactive state store
├── Task 5: Extract tab/navigation state
└── Task 6: Extract tree selection state

Wave 3 (UI Components):
├── Task 7: Create ArchitectureTabBar.svelte
├── Task 8: Create ArchitectureLoading.svelte (skeleton)
├── Task 9: Create ArchitectureError.svelte (retry)
└── Task 10: Create ArchitectureLayout.svelte

Wave 4 (Integration):
├── Task 11: Refactor +page.svelte to use new modules
├── Task 12: Add skeleton screens
└── Task 13: Add error retry logic

Wave 5 (Optimization):
├── Task 14: Add data caching
├── Task 15: Add loading debounce
└── Task 16: Performance testing

Wave FINAL (Verification):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review
├── Task F3: Real manual QA
└── Task F4: Scope fidelity check
```

---

## TODOs

- [ ] 1. Create architectureStore.ts — data loading and caching

  **What to do**:
  - Create `src/lib/stores/pm/architectureStore.ts`
  - Implement `loadArchitectureData(projectId)` function
  - Use `Promise.allSettled` for parallel API calls
  - Implement simple in-memory cache (Map)
  - Export reactive state: `parameterEntries`, `archEntries`, `isLoading`, `loadError`

  **Must NOT do**:
  - Do not change API endpoints
  - Do not add external dependencies

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: None

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Blocks**: Task 11 (Integration)

  **References**:
  - `src/lib/apis/pm/index.ts:getEntries` — API function
  - Current `+page.svelte` lines 70-108 — loadData logic

  **Acceptance Criteria**:
  - Store loads data correctly
  - Cache prevents duplicate API calls
  - TypeScript types are complete

  **QA Scenarios**:
  ```
  Scenario: Data loads successfully
    Tool: Bun test
    Steps:
      1. Import store and call loadArchitectureData
      2. Verify parameterEntries and archEntries are populated
    Expected Result: Data loaded, isLoading = false
  ```

- [ ] 2. Create architectureService.ts — business logic

  **What to do**:
  - Create `src/lib/services/architectureService.ts`
  - Extract `aggregateModuleFeatureTree` function
  - Extract MindMap node CRUD operations
  - Extract module/feature management functions

  **Must NOT do**:
  - Do not change business logic behavior

  **Recommended Agent Profile**:
  - **Category**: `quick`

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 1)

  **References**:
  - Current `+page.svelte` lines 116-174 — aggregateModuleFeatureTree
  - Current `+page.svelte` lines 245-357 — CRUD operations

- [ ] 3. Extract data transformation functions

  **What to do**:
  - Extract `aggregateModuleFeatureTree` to service
  - Extract `getEntryData` helper
  - Extract `statusMap` and other constants

  **Recommended Agent Profile**:
  - **Category**: `quick`

- [ ] 4. Create reactive state store

  **What to do**:
  - Create `src/lib/stores/pm/architectureState.ts`
  - Manage `activeTab`, `selectedModule`, `selectedFeature`
  - Implement cross-tab navigation state sync

  **Recommended Agent Profile**:
  - **Category**: `quick`

- [ ] 5. Create ArchitectureTabBar.svelte

  **What to do**:
  - Create `src/lib/components/pm/architecture/ArchitectureTabBar.svelte`
  - Props: `activeTab`, `onTabChange`
  - Use project design system (Tailwind classes)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`

- [ ] 6. Create ArchitectureLoading.svelte

  **What to do**:
  - Create skeleton screen component
  - Match existing table layout
  - Use animate-pulse for loading effect

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`

- [ ] 7. Create ArchitectureError.svelte

  **What to do**:
  - Create error display component
  - Add retry button
  - Props: `error`, `onRetry`

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`

- [ ] 8. Refactor +page.svelte

  **What to do**:
  - Import and use new stores and components
  - Reduce file to < 200 lines
  - Keep all existing functionality

  **Recommended Agent Profile**:
  - **Category**: `deep`

- [ ] 9. Add data caching

  **What to do**:
  - Implement simple Map-based cache in store
  - Cache key: `projectId`
  - Add cache invalidation on data change

  **Recommended Agent Profile**:
  - **Category**: `quick`

- [ ] 10. Add error retry logic

  **What to do**:
  - Add retry button to error component
  - Implement exponential backoff (optional)
  - Show retry count

  **Recommended Agent Profile**:
  - **Category**: `quick`

---

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Verify all deliverables exist and +page.svelte < 200 lines.

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run build, lint, type-check.

- [ ] F3. **Real Manual QA** — `unspecified-high`
  Test loading, tab switching, data display, error handling.

- [ ] F4. **Scope Fidelity Check** — `deep`
  Verify no functionality was lost in refactoring.

---

## Commit Strategy

- Commit 1: `refactor(architecture): extract data layer`
- Commit 2: `refactor(architecture): extract business logic`
- Commit 3: `refactor(architecture): add UI components`
- Commit 4: `refactor(architecture): integrate and optimize`

---

## Success Criteria

### Verification Commands
```bash
npm run build
npm run lint
npx svelte-check --tsconfig ./tsconfig.json
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] +page.svelte < 200 lines
- [ ] No TypeScript errors
- [ ] No build errors
