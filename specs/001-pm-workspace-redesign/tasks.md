# Tasks: PM 工作台重构 — 模块化布局与差异化编辑器

**Input**: Design documents from `/specs/001-pm-workspace-redesign/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL — only include if explicitly requested.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create PM component directory structure: `src/lib/components/pm/`
- [X] T002 [P] Create PM API directory structure: `src/lib/apis/pm/`
- [X] T003 [P] Create PM store directory structure: `src/lib/stores/pm/`
- [X] T004 [P] Create PM route directory structure: `src/routes/(app)/pm/`
- [X] T005 Install TipTap dependencies: `@tiptap/core`, `@tiptap/starter-kit`, `@tiptap/extension-markdown`
- [X] T006 Install @xyflow/svelte for mindmap rendering
- [X] T007 Install zod for form validation
- [X] T008 Create base PM types file: `src/lib/apis/pm/types.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T009 Create `PMModuleNav.svelte` — sidebar navigation with 4 categories (planning/design/execution/review)
- [X] T010 Create `PMProjectHeader.svelte` — project header with name, current version, version selector
- [X] T011 Create `PMVersionSelector.svelte` — version dropdown with search/filter
- [X] T012 Create base store: `src/lib/stores/pm/projectStore.ts` — current project state
- [X] T013 Create base store: `src/lib/stores/pm/versionStore.ts` — current version state
- [X] T014 Create base store: `src/lib/stores/pm/moduleStore.ts` — current module state
- [X] T015 Create base API: `src/lib/apis/pm/index.ts` — HTTP client wrapper
- [X] T016 Create base API: `src/lib/apis/pm/modules/prd.ts` — PRD module CRUD
- [X] T017 Create base API: `src/lib/apis/pm/modules/requirement.ts` — requirement module CRUD
- [X] T018 Create base API: `src/lib/apis/pm/modules/parameter.ts` — parameter module CRUD
- [X] T019 Create base API: `src/lib/apis/pm/modules/testcase.ts` — testcase module CRUD
- [X] T020 Create base API: `src/lib/apis/pm/modules/risk.ts` — risk module CRUD
- [X] T021 Create base API: `src/lib/apis/pm/modules/competitor.ts` — competitor module CRUD
- [X] T022 Create base API: `src/lib/apis/pm/modules/roadmap.ts` — roadmap module CRUD
- [X] T023 Create base API: `src/lib/apis/pm/modules/meeting.ts` — meeting module CRUD
- [X] T024 Create base API: `src/lib/apis/pm/modules/acceptance.ts` — acceptance module CRUD
- [X] T025 Create base API: `src/lib/apis/pm/modules/faq.ts` — FAQ module CRUD
- [X] T026 Create base API: `src/lib/apis/pm/modules/product-architecture.ts` — product architecture module CRUD
- [X] T027 Create base API: `src/lib/apis/pm/version.ts` — version management CRUD
- [X] T028 Create base API: `src/lib/apis/pm/relation.ts` — relation management CRUD
- [X] T029 Create base API: `src/lib/apis/pm/agent.ts` — agent analysis API
- [X] T030 Create base layout: `src/routes/(app)/pm/+layout.svelte` — sidebar + header layout
- [X] T031 Create base page: `src/routes/(app)/pm/+page.svelte` — default redirect to first module
- [X] T032 Create module page: `src/routes/(app)/pm/[module]/+page.svelte` — dynamic module routing

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Sidebar Navigation (Priority: P1) 🎯 MVP

**Goal**: Implement categorized sidebar navigation with expand/collapse

**Independent Test**: Open PM workspace, sidebar shows 4 categories with submenus, clicking navigates to correct module

### Implementation for User Story 1

- [X] T033 [P] [US1] Implement sidebar category data structure in `src/lib/stores/pm/moduleStore.ts`
- [X] T034 [P] [US1] Create `PMModuleNav.svelte` with expandable/collapsible categories
- [X] T035 [US1] Add active module highlighting in sidebar
- [X] T036 [US1] Implement URL sync on module navigation (`/pm/[module]`)
- [X] T037 [US1] Add empty state for modules with no entries
- [X] T038 [US1] Implement responsive sidebar (collapse on mobile)

**Checkpoint**: Sidebar navigation fully functional, all 10 modules accessible

---

## Phase 4: User Story 2 — Differentiated Editors (Priority: P1) 🎯 MVP

**Goal**: Implement differentiated editors for each module type

**Independent Test**: Open PRD/parameter/risk modules, verify different editor types and field structures

### Implementation for User Story 2

- [X] T039 [P] [US2] Create `PMRichEditor.svelte` — TipTap-based rich text editor
- [X] T040 [P] [US2] Create `PMFormEditor.svelte` — structured form editor with zod validation
- [X] T041 [P] [US2] Create `PMMixedEditor.svelte` — form + rich text hybrid editor
- [X] T042 [P] [US2] Create `PMMindMap.svelte` — @xyflow/svelte mindmap editor
- [X] T043 [US2] Implement PRD module form (title, version, status, rich text, attachments)
- [X] T044 [US2] Implement requirement module form (source, category, tags, userRole, expectedBenefit)
- [X] T045 [US2] Implement parameter module form (key, paramType, dataType, required, defaultValue)
- [X] T046 [US2] Implement testcase module form (scenario, precondition, steps, expectedResult, caseType)
- [X] T047 [US2] Implement risk module form (probability, impactScope, owner, measures, deadline + rich text)
- [X] T048 [US2] Implement competitor module form (name, url, description, dimensions)
- [X] T049 [US2] Implement roadmap module form (mindmap nodes, layout selection)
- [X] T050 [US2] Implement meeting module form (participants, meetingDate, conclusions, actionItems)
- [X] T051 [US2] Implement acceptance module form (scope, result, passedItems, 遗留问题)
- [X] T052 [US2] Implement FAQ module form (question, answer, audience, relatedFeatures)
- [X] T053 [US2] Implement product-architecture module form (mindmap nodes, autoExtracted)
- [X] T054 [US2] Add old data migration logic (auto-detect `{text: string}` format, convert with defaults)
- [X] T055 [US2] Create `PMMigrationPanel.svelte` for migration summary and confirmation

**Checkpoint**: All 10 modules have differentiated editors, old data migrated

---

## Phase 5: User Story 3 — Version Control (Priority: P1) 🎯 MVP

**Goal**: Implement project header with version switching

**Independent Test**: Switch versions, all module data refreshes correctly

### Implementation for User Story 3

- [X] T056 [P] [US3] Create `PMProjectHeader.svelte` with project name, current version, version selector
- [X] T057 [P] [US3] Implement version dropdown with search/filter for 100+ versions
- [X] T058 [US3] Add version creation flow (snapshot with incremental marking)
- [X] T059 [US3] Implement version switching with data refresh
- [X] T060 [US3] Add "unsaved changes" prompt on version switch
- [X] T061 [US3] Implement version comparison view (diff display)
- [X] T062 [US3] Implement version rollback (project-level and module-level)

**Checkpoint**: Version control fully functional, can create/switch/compare/rollback

---

## Phase 6: User Story 4 — Data Interconnection & Traceability (Priority: P2)

**Goal**: Implement cross-module relations and bidirectional traceability

**Independent Test**: Create parameter linked to PRD, verify bidirectional visibility

### Implementation for User Story 4

- [X] T063 [P] [US4] Create `PMRelationPicker.svelte` — dropdown for selecting related entities
- [X] T064 [P] [US4] Implement relation CRUD API (`src/lib/apis/pm/relation.ts`)
- [X] T065 [US4] Add relation fields to parameter form (sourcePRD)
- [X] T066 [US4] Add relation fields to testcase form (requirementId, parameterId)
- [X] T067 [US4] Add relation display in PRD view (linked parameters, testcases)
- [X] T068 [US4] Implement impact analysis view (upstream/downstream traversal)
- [X] T069 [US4] Implement traceability graph visualization
- [X] T070 [US4] Handle deleted entity references (show "[已删除的PRD]")

**Checkpoint**: Cross-module relations working, bidirectional traceability visible

---

## Phase 7: User Story 5 — Agent Intelligence Upgrade (Priority: P3)

**Goal**: Implement AI-assisted analysis with manual + auto trigger

**Independent Test**: Trigger Agent analysis, receive actionable suggestions

### Implementation for User Story 5

- [X] T071 [P] [US5] Create `PMAgentPanel.svelte` — AI suggestion panel
- [X] T072 [P] [US5] Implement manual trigger button ("AI分析") in each module
- [X] T073 [US5] Implement auto-trigger on save (configurable in settings)
- [X] T074 [US5] Implement Agent config store (`src/lib/stores/pm/agentStore.ts`)
- [X] T075 [US5] Implement PRD completeness analysis (missing sections, incomplete logic)
- [X] T076 [US5] Implement risk identification analysis (based on historical data)
- [X] T077 [US5] Implement requirement-testcase association suggestions
- [X] T078 [US5] Add suggestion confirmation flow (confirm/reject)
- [X] T079 [US5] Implement suggestion history tracking

**Checkpoint**: Agent provides actionable suggestions, user can confirm/reject

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T080 [P] Performance optimization: virtual scrolling for 1000+ rows
- [X] T081 [P] Rich text editor performance: lazy loading for 50,000-word documents
- [X] T082 [P] Mindmap performance: node virtualization for large graphs
- [X] T083 [P] Accessibility: keyboard navigation for sidebar
- [X] T084 [P] Accessibility: ARIA labels for all interactive elements
- [X] T085 [P] Error handling: graceful degradation when AI service unavailable
- [X] T086 [P] Error handling: fallback to plaintext when rich text editor fails
- [X] T087 Documentation: update `docs/pm-workspace.md` with new features
- [X] T088 Documentation: add PM module developer guide
- [X] T089 Run quickstart.md validation scenarios
- [X] T090 Final integration testing across all user stories

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1, US2, US3 can proceed in parallel (P1 priority)
  - US4 depends on US2 completion (needs differentiated editors)
  - US5 depends on US2 completion (needs module content to analyze)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

| Story | Dependencies | Can Start After |
|-------|-------------|-----------------|
| US1 (Sidebar) | Foundational | Phase 2 complete |
| US2 (Editors) | Foundational | Phase 2 complete |
| US3 (Version) | Foundational | Phase 2 complete |
| US4 (Relations) | US2 complete | US2 done |
| US5 (Agent) | US2 complete | US2 done |

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- US1, US2, US3 can be worked on in parallel by different team members
- US4 and US5 can be worked on in parallel after US2 complete

---

## Implementation Strategy

### MVP First (User Story 1-3 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 — Sidebar Navigation
4. Complete Phase 4: US2 — Differentiated Editors
5. Complete Phase 5: US3 — Version Control
6. **STOP and VALIDATE**: Test all P1 stories independently
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 → Test independently → Deploy/Demo (MVP v0.1)
3. Add US2 → Test independently → Deploy/Demo (MVP v0.2)
4. Add US3 → Test independently → Deploy/Demo (MVP v0.3)
5. Add US4 → Test independently → Deploy/Demo (v1.0)
6. Add US5 → Test independently → Deploy/Demo (v1.1)
7. Polish → Final release (v1.0)

---

## Task Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 1: Setup | T001-T008 | Directory structure, dependencies, base types |
| Phase 2: Foundational | T009-T032 | Sidebar, header, stores, APIs, layout, routing |
| Phase 3: US1 | T033-T038 | Sidebar navigation with categories |
| Phase 4: US2 | T039-T055 | Differentiated editors for all modules |
| Phase 5: US3 | T056-T062 | Version control (create/switch/compare/rollback) |
| Phase 6: US4 | T063-T070 | Cross-module relations and traceability |
| Phase 7: US5 | T071-T079 | Agent intelligence upgrade |
| Phase 8: Polish | T080-T090 | Performance, accessibility, documentation |

**Total Tasks**: 90
**MVP Tasks (P1 only)**: 62 (Phases 1-5)
**Estimated Duration**: 4-6 weeks (MVP), 6-8 weeks (full feature)

---

## Phase 9: v3 Enhancement — Version Tracking, Editor Customization, Annotation, Traceability

**Purpose**: Implement spec-v3 requirements for global version tracking, editor version control, diff/merge, annotation, and PRD sync

### Phase 9a: Version Tracking — Filter/Sort/Pagination + Version Badges

- [X] T091 Add filter state variables (filterStatus, filterPriority, filterVersion) to module page
- [X] T092 Implement filteredAndSorted derived logic with multi-filter + sort support
- [X] T093 Add filter bar UI (status/priority/version dropdowns + sort buttons) to module page template
- [X] T094 Add pagination state (currentPage, PAGE_SIZE, totalPages, pagedEntries) and UI
- [X] T095 Add version badge column to table view (PMVersionHistoryDropdown per row)
- [X] T096 Add versionOptions derived list for version filter dropdown

### Phase 9b: Editor Version Control — Auto-save vs Manual-save

- [X] T097 Add auto-save state variables (autoSaveTimer, saveStatus, lastAutoSaveTime) to module page
- [X] T098 Implement triggerAutoSave (30s debounce) and saveEntryContentOnly functions
- [X] T099 Modify saveEntryDoc to open PMSaveVersionDialog instead of auto-creating version
- [X] T100 Create PMSaveVersionDialog.svelte — save version confirmation modal
- [X] T101 Add saveAsNewVersion function that creates EntryVersion
- [X] T102 Add PMSaveVersionDialog import and template rendering
- [X] T103 Add save status display in editor header (unsaved/auto-saving/auto-saved at HH:MM)

### Phase 9c: Version Compare — Side-by-side Red/Green Diff

- [X] T104 Create pmDiff.ts — Myers diff algorithm with HTML stripping
- [X] T105 Rewrite PMVersionComparePanel.svelte with side-by-side layout
- [X] T106 Implement green/red diff line rendering with line numbers and gutter markers
- [X] T107 Implement synced scroll between left and right panels

### Phase 9d: Version Merge — Line-level Selection

- [X] T108 Rewrite PMVersionMergePanel.svelte with branch selection → conflict detection flow
- [X] T109 Implement per-conflict resolution (source/target choice)
- [X] T110 Add batch resolve (全部采用分支/全部采用主线) for multi-line selection

### Phase 9e: Annotation Feature

- [X] T111 Add EntryAnnotation type to types.ts
- [X] T112 Create pmAnnotationExtension.ts — TipTap custom Mark (highlight yellow)
- [X] T113 Create PMAnnotationPanel.svelte — annotation list side panel
- [X] T114 Integrate AnnotationExtension into pmTiptapConfig.ts
- [X] T115 Integrate annotation support into PMRichEditor.svelte (setAnnotation, PMAnnotationPanel, floating button)

### Phase 9f: Traceability Enhancement

- [X] T116 Rewrite PMTraceabilityGraph.svelte with entity-type-specific colors/labels
- [X] T117 Add relation type filter to traceability graph
- [X] T118 Add version badge on graph nodes (entries prop lookup)
- [X] T119 Add versionSnapshot to relation creation in traceability graph
- [X] T120 Add PMTraceabilityGraph component + "查看溯源图" button to module page trace panel

### Phase 9g: PRD Sync & Verification

- [X] T121 Add versionSnapshot field to Relation type in types.ts
- [X] T122 Create spec-v3.md specification document
- [X] T123 Create requirements-v3.md checklist
- [X] T124 Build verification (vite build passes with no errors)
- [X] T125 FR-001 through FR-020 verification — all 20 requirements confirmed implemented

---

## v3 Task Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 9a | T091-T096 | Filter/sort/pagination + version badges |
| Phase 9b | T097-T103 | Auto-save vs manual-save version control |
| Phase 9c | T104-T107 | Side-by-side red/green diff |
| Phase 9d | T108-T110 | Line-level merge with batch select |
| Phase 9e | T111-T115 | Annotation feature (TipTap Mark + panel) |
| Phase 9f | T116-T120 | Traceability enhancement (version badges, filters) |
| Phase 9g | T121-T125 | PRD sync & build verification |

**v3 Tasks**: 35
**Status**: All completed
