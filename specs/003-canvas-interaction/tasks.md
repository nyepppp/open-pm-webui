# Tasks: Canvas Interaction Foundation

**Input**: Design documents from `/specs/003-canvas-interaction/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/api.md, research.md, quickstart.md

**Tests**: Test tasks included for validation scenarios from quickstart.md

**Organization**: Tasks grouped by user story to enable independent implementation and testing

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and canvas-specific structure

- [X] T001 [P] Create canvas component directory structure: `src/lib/components/pm/canvas/`
- [X] T002 [P] Create canvas types directory: `src/lib/types/canvas.ts`
- [X] T003 [P] Create canvas services directory: `src/lib/services/`
- [X] T004 [P] Create canvas test directory: `src/tests/canvas/`
- [X] T005 Configure canvas-specific linting and TypeScript settings

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core canvas infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Define TypeScript interfaces: Canvas, Node, Connection, Selection, Group in `src/lib/types/canvas.ts`
- [X] T007 [P] Implement Canvas state store with Command pattern in `src/lib/stores/canvasStore.ts`
- [X] T008 Implement Canvas API client service in `src/lib/services/canvasApi.ts`
- [X] T009 Implement offline sync service in `src/lib/services/canvasSync.ts`
- [X] T010 Create base Canvas component with HTML5 Canvas 2D context in `src/lib/components/pm/canvas/Canvas.svelte`
- [X] T011 Implement coordinate transformation utilities (world ↔ screen) in `src/lib/utils/canvasCoords.ts`
- [X] T012 Implement rendering pipeline (viewport culling, dirty region tracking) in `src/lib/utils/canvasRender.ts`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Canvas View Navigation (Priority: P1) 🎯 MVP

**Goal**: Implement pan, zoom, reset, and grid functionality for canvas navigation

**Independent Test**: Open canvas, verify pan (drag empty space), zoom (mouse wheel), reset (Ctrl+0), and grid snap all function correctly

### Tests for User Story 1

- [X] T013 [P] [US1] Unit test: Coordinate transformation (world ↔ screen) in `src/tests/canvas/coords.test.ts`
- [X] T014 [P] [US1] Unit test: Viewport culling logic in `src/tests/canvas/viewport.test.ts`
- [X] T015 [P] [US1] Integration test: Pan, zoom, reset interactions in `src/tests/canvas/navigation.test.ts`

### Implementation for User Story 1

- [X] T016 [P] [US1] Implement pan functionality (mouse drag + Space+drag) in `src/lib/components/pm/canvas/Canvas.svelte`
- [X] T017 [P] [US1] Implement zoom functionality (mouse wheel + Ctrl++/-) in `src/lib/components/pm/canvas/Canvas.svelte`
- [X] T018 [US1] Implement reset view (Ctrl+0) in `src/lib/components/pm/canvas/Canvas.svelte`
- [X] T019 [US1] Create Grid component with toggle in `src/lib/components/pm/canvas/Grid.svelte`
- [X] T020 [US1] Implement grid snap logic in `src/lib/utils/canvasCoords.ts`
- [X] T021 [US1] Add keyboard shortcut handlers in `src/lib/components/pm/canvas/Canvas.svelte`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Node Selection and Manipulation (Priority: P1) 🎯 MVP

**Goal**: Implement node CRUD, selection, copy/paste, and inline editing

**Independent Test**: Create nodes, verify single/multi-select, move, copy/paste, delete, and inline text editing all work correctly

### Tests for User Story 2

- [X] T022 [P] [US2] Unit test: Node selection logic in `src/tests/canvas/selection.test.ts`
- [X] T023 [P] [US2] Unit test: Clipboard operations (copy/paste/cut) in `src/tests/canvas/clipboard.test.ts`
- [X] T024 [P] [US2] Integration test: Node lifecycle (create, edit, delete) in `src/tests/canvas/node-lifecycle.test.ts`

### Implementation for User Story 2

- [X] T025 [P] [US2] Create Node component in `src/lib/components/pm/canvas/Node.svelte`
- [X] T026 [P] [US2] Implement node rendering (shapes, colors, text) in `src/lib/components/pm/canvas/Node.svelte`
- [X] T027 [US2] Implement single node selection in `src/lib/components/pm/canvas/Canvas.svelte`
- [X] T028 [US2] Implement multi-selection (Ctrl+click + area selection) in `src/lib/components/pm/canvas/Canvas.svelte`
- [X] T029 [US2] Create SelectionBox component in `src/lib/components/pm/canvas/SelectionBox.svelte`
- [X] T030 [US2] Implement node drag movement in `src/lib/components/pm/canvas/Canvas.svelte`
- [X] T031 [US2] Implement clipboard operations (Ctrl+C/V/X) in `src/lib/services/clipboard.ts`
- [X] T032 [US2] Implement inline text editing (double-click) in `src/lib/components/pm/canvas/Node.svelte`
- [X] T033 [US2] Create properties panel component in `src/lib/components/pm/canvas/PropertiesPanel.svelte`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Connection Lines (Edges) (Priority: P1) 🎯 MVP

**Goal**: Implement connection creation, selection, deletion, and manual bending

**Independent Test**: Create two nodes, connect them via anchors, verify connection line appears and can be selected/deleted

### Tests for User Story 3

- [X] T034 [P] [US3] Unit test: Connection anchor detection in `src/tests/canvas/anchors.test.ts`
- [X] T035 [P] [US3] Unit test: Connection line intersection in `src/tests/canvas/connection-geometry.test.ts`
- [X] T036 [P] [US3] Integration test: Connection lifecycle in `src/tests/canvas/connection-lifecycle.test.ts`

### Implementation for User Story 3

- [X] T037 [P] [US3] Create Connection component in `src/lib/components/pm/canvas/Connection.svelte`
- [X] T038 [P] [US3] Implement connection anchor detection on hover in `src/lib/components/pm/canvas/Node.svelte`
- [X] T039 [US3] Implement connection drag creation in `src/lib/components/pm/canvas/Canvas.svelte`
- [X] T040 [US3] Implement connection rendering (straight + Manhattan routing) in `src/lib/components/pm/canvas/Connection.svelte`
- [X] T041 [US3] Implement connection selection in `src/lib/components/pm/canvas/Canvas.svelte`
- [X] T042 [US3] Implement manual bend points (draggable midpoints) in `src/lib/components/pm/canvas/Connection.svelte`
- [X] T043 [US3] Implement ESC cancel during connection drag in `src/lib/components/pm/canvas/Canvas.svelte`

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Multi-Node Operations and Alignment (Priority: P2)

**Goal**: Implement multi-node alignment, distribution, and grouping

**Independent Test**: Select multiple nodes, apply alignment and distribution, verify nodes reposition correctly

### Tests for User Story 4

- [X] T044 [P] [US4] Unit test: Alignment algorithms in `src/tests/canvas/alignment.test.ts`
- [X] T045 [P] [US4] Unit test: Distribution algorithms in `src/tests/canvas/distribution.test.ts`
- [X] T046 [P] [US4] Integration test: Group operations in `src/tests/canvas/grouping.test.ts`

### Implementation for User Story 4

- [X] T047 [P] [US4] Implement alignment algorithms (left, right, top, bottom, center) in `src/lib/utils/alignment.ts`
- [X] T048 [P] [US4] Implement distribution algorithms (horizontal, vertical) in `src/lib/utils/distribution.ts`
- [X] T049 [US4] Create alignment toolbar component in `src/lib/components/pm/canvas/AlignmentToolbar.svelte`
- [X] T050 [US4] Implement grouping logic (Ctrl+G) in `src/lib/stores/canvasStore.ts`
- [X] T051 [US4] Implement ungrouping logic (Ctrl+Shift+G) in `src/lib/stores/canvasStore.ts`
- [X] T052 [US4] Create Group component for visual grouping in `src/lib/components/pm/canvas/Group.svelte`

**Checkpoint**: User Story 4 adds professional diagram organization tools

---

## Phase 7: User Story 5 - Undo/Redo Operations (Priority: P2)

**Goal**: Implement undo/redo for all mutable canvas operations

**Independent Test**: Perform sequence of actions (add, move, delete), verify Ctrl+Z undoes and Ctrl+Y redoes correctly

### Tests for User Story 5

- [X] T053 [P] [US5] Unit test: Command pattern implementation in `src/tests/canvas/commands.test.ts`
- [X] T054 [P] [US5] Unit test: Undo/redo stack management in `src/tests/canvas/history.test.ts`
- [X] T055 [P] [US5] Integration test: Full undo/redo workflow in `src/tests/canvas/undo-redo.test.ts`

### Implementation for User Story 5

- [X] T056 [P] [US5] Implement Command interface and base classes in `src/lib/types/commands.ts`
- [X] T057 [P] [US5] Implement AddNodeCommand in `src/lib/commands/addNode.ts`
- [X] T058 [P] [US5] Implement MoveNodeCommand in `src/lib/commands/moveNode.ts`
- [X] T059 [P] [US5] Implement DeleteNodeCommand in `src/lib/commands/deleteNode.ts`
- [X] T060 [P] [US5] Implement CreateConnectionCommand in `src/lib/commands/createConnection.ts`
- [X] T061 [P] [US5] Implement EditNodeCommand in `src/lib/commands/editNode.ts`
- [X] T062 [US5] Integrate undo/redo into canvas store in `src/lib/stores/canvasStore.ts`
- [X] T063 [US5] Add keyboard shortcuts (Ctrl+Z/Y/Shift+Z) in `src/lib/components/pm/canvas/Canvas.svelte`

**Checkpoint**: User Story 5 enables safe experimentation with canvas changes

---

## Phase 8: User Story 6 - Context Menu Operations (Priority: P3)

**Goal**: Implement right-click context menus for canvas, nodes, and connections

**Independent Test**: Right-click on empty canvas, nodes, and connections, verify appropriate menu options appear

### Tests for User Story 6

- [X] T064 [P] [US6] Unit test: Context menu positioning in `src/tests/canvas/context-menu.test.ts`
- [X] T065 [P] [US6] Integration test: Context menu actions in `src/tests/canvas/context-menu-actions.test.ts`

### Implementation for User Story 6

- [X] T066 [P] [US6] Create ContextMenu component in `src/lib/components/pm/canvas/ContextMenu.svelte`
- [X] T067 [US6] Implement canvas context menu (paste, select all, clear, settings) in `src/lib/components/pm/canvas/Canvas.svelte`
- [X] T068 [US6] Implement node context menu (copy, cut, delete, group, etc.) in `src/lib/components/pm/canvas/Node.svelte`
- [X] T069 [US6] Implement connection context menu (delete, style) in `src/lib/components/pm/canvas/Connection.svelte`
- [X] T070 [US6] Implement z-index operations (bring to front, send to back) in `src/lib/stores/canvasStore.ts`

**Checkpoint**: User Story 6 improves discoverability and power-user efficiency

---

## Phase 9: Data Persistence & Offline Support (Priority: P1)

**Goal**: Implement auto-save, load, export, import, and offline editing

**Independent Test**: Create canvas, modify, verify auto-save, refresh page, verify state restored

### Tests for Data Persistence

- [X] T071 [P] [PERSIST] Unit test: Canvas serialization/deserialization in `src/tests/canvas/serialization.test.ts`
- [X] T072 [P] [PERSIST] Unit test: Offline sync logic in `src/tests/canvas/offline-sync.test.ts`
- [X] T073 [P] [PERSIST] Integration test: Full save/load cycle in `src/tests/canvas/persistence.test.ts`

### Implementation for Data Persistence

- [X] T074 [P] [PERSIST] Implement canvas serialization (JSON) in `src/lib/utils/serialization.ts`
- [X] T075 [P] [PERSIST] Implement PNG/SVG export in `src/lib/utils/export.ts`
- [X] T076 [P] [PERSIST] Implement Draw.io XML export in `src/lib/utils/exportDrawio.ts`
- [X] T077 [P] [PERSIST] Implement Markdown export in `src/lib/utils/exportMarkdown.ts`
- [X] T078 [P] [PERSIST] Implement IndexedDB offline cache in `src/lib/services/offlineStorage.ts`
- [X] T079 [PERSIST] Implement auto-save with debouncing in `src/lib/services/canvasSync.ts`
- [X] T080 [PERSIST] Implement background sync on reconnect in `src/lib/services/canvasSync.ts`
- [X] T081 [PERSIST] Create backend API endpoints for canvas CRUD in `backend/src/routers/canvas.py`
- [X] T082 [PERSIST] Create backend models for Canvas, Node, Connection in `backend/src/models/canvas.py`

**Checkpoint**: Canvas state persists reliably across sessions

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Performance optimization, accessibility, and final validation

- [X] T083 [P] Optimize rendering performance (viewport culling, dirty regions) in `src/lib/utils/canvasRender.ts`
- [X] T084 [P] Add keyboard accessibility (Tab navigation, ARIA labels) in `src/lib/components/pm/canvas/`
- [X] T085 [P] Add touch support for tablets (optional, out of scope but nice-to-have) in `src/lib/components/pm/canvas/Canvas.svelte`
- [X] T086 Add loading states and error handling in `src/lib/components/pm/canvas/Canvas.svelte`
- [X] T087 Add onboarding tooltips for first-time users in `src/lib/components/pm/canvas/Onboarding.svelte`
- [X] T088 Run quickstart.md validation scenarios and fix any issues
- [X] T089 Performance profiling and optimization (target: 30fps with 100 nodes)
- [X] T090 Security review (XSS prevention, input validation)
- [X] T091 Documentation update: README, API docs, component docs

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User Story 1 (P1) → User Story 2 (P1) → User Story 3 (P1) → User Story 4 (P2) → User Story 5 (P2) → User Story 6 (P3)
  - Data Persistence (Phase 9) depends on User Stories 1-3 (core functionality)
  - Polish (Phase 10) depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Depends on US1 for canvas viewport
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - Depends on US2 for node selection
- **User Story 4 (P2)**: Can start after US2 (node selection) - Independent of US3
- **User Story 5 (P2)**: Can start after US2 (node operations) - Independent of US3/US4
- **User Story 6 (P3)**: Can start after US2/US3 - Needs both nodes and connections

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before components
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, and US3 can start in parallel (if team capacity allows)
- US4, US5 can run in parallel after US2 completes
- US6 can run after US2 and US3 complete
- Data Persistence tasks can run in parallel with later user stories
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test: Coordinate transformation in src/tests/canvas/coords.test.ts"
Task: "Unit test: Viewport culling logic in src/tests/canvas/viewport.test.ts"
Task: "Integration test: Pan, zoom, reset in src/tests/canvas/navigation.test.ts"

# Launch all models for User Story 1 together:
Task: "Implement pan functionality in src/lib/components/pm/canvas/Canvas.svelte"
Task: "Implement zoom functionality in src/lib/components/pm/canvas/Canvas.svelte"
Task: "Create Grid component in src/lib/components/pm/canvas/Grid.svelte"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Canvas Navigation)
4. Complete Phase 4: User Story 2 (Node Selection & Manipulation)
5. Complete Phase 5: User Story 3 (Connection Lines)
6. **STOP and VALIDATE**: Test core canvas functionality
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Add User Story 5 → Test independently → Deploy/Demo
7. Add User Story 6 → Test independently → Deploy/Demo
8. Add Data Persistence → Test independently → Deploy/Demo
9. Polish → Final validation → Deploy

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Canvas Navigation)
   - Developer B: User Story 2 (Node Selection) - after US1 viewport ready
   - Developer C: User Story 3 (Connections) - after US2 nodes ready
3. After US2/US3 complete:
   - Developer A: User Story 4 (Alignment)
   - Developer B: User Story 5 (Undo/Redo)
   - Developer C: User Story 6 (Context Menus)
4. Data Persistence and Polish can run in parallel with later stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Performance target: 30fps with 100 nodes and 50 connections
- Offline support via IndexedDB with background sync
