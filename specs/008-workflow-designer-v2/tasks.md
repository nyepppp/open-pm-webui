# Tasks: Workflow Designer V2 - Global Access & AI Integration

**Input**: Design documents from `/specs/008-workflow-designer-v2/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 [P] Add Svelte Flow dependency to package.json
- [x] T002 [P] Add xmltodict dependency to backend/requirements.txt
- [x] T003 Create database migration for workflow tables: `backend/open_webui/migrations/versions/add_workflow_tables.py`
- [x] T004 Create workflow directory structure: `src/routes/(app)/workflows/`, `backend/open_webui/routers/workflows.py`, `backend/open_webui/services/workflow/`
- [x] T005 Update global sidebar to include "Workflows" entry: `src/lib/components/layout/Sidebar.svelte`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 [P] Create SQLAlchemy models for Workflow, WorkflowNode, WorkflowEdge: `backend/open_webui/models/workflows.py`
- [x] T007 [P] Create SQLAlchemy models for WorkflowExecution, ExecutionLog: `backend/open_webui/models/workflows.py`
- [x] T008 [P] Create SQLAlchemy models for WorkflowTemplate, WorkflowExport: `backend/open_webui/models/workflows.py`
- [x] T009 Implement workflow CRUD API endpoints: `backend/open_webui/routers/workflows.py`
- [x] T010 Implement workflow execution engine (server-side): `backend/open_webui/services/workflow/engine.py`
- [x] T011 Implement WebSocket handler for execution streaming: `backend/open_webui/services/workflow/websocket.py`
- [x] T012 Create workflow TypeScript types: `src/lib/apis/workflow/types.ts`
- [x] T013 Create workflow API client functions: `src/lib/apis/workflow/index.ts`
- [x] T014 Create workflow Svelte store: `src/lib/stores/workflowStore.ts`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Global Workflow Access (Priority: P1) 🎯 MVP

**Goal**: Make workflow designer globally accessible from OpenWebUI sidebar

**Independent Test**: Verify "Workflows" appears in sidebar, clicking opens workflow list, can create and save a workflow

### Implementation for User Story 1

- [x] T015 [US1] Create workflow list page route: `src/routes/(app)/workflows/+page.svelte`
- [x] T016 [US1] Create WorkflowList component: `src/lib/components/workflow/WorkflowList.svelte`
- [x] T017 [US1] Create workflow designer page route: `src/routes/(app)/workflows/[workflowId]/+page.svelte`
- [x] T018 [US1] Implement global sidebar "Workflows" menu item with icon: `src/lib/components/layout/Sidebar.svelte`
- [x] T019 [US1] Add workflow search and filter functionality: `src/lib/components/workflow/WorkflowList.svelte`
- [x] T020 [US1] Implement cross-project workflow sharing: `backend/open_webui/routers/workflows.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - AI-Assisted Workflow Generation (Priority: P1)

**Goal**: Allow users to generate workflows from natural language descriptions

**Independent Test**: Enter "Create a content moderation pipeline" and verify AI generates appropriate nodes

### Implementation for User Story 2

- [x] T021 [P] [US2] Create AI generation service: `backend/open_webui/services/workflow/ai_generator.py`
- [x] T022 [P] [US2] Create AI generation API endpoint: `backend/open_webui/routers/workflows.py`
- [x] T023 [US2] Create AIGenerateModal component: `src/lib/components/workflow/AIGenerateModal.svelte`
- [x] T024 [US2] Integrate AI generation into designer toolbar: `src/lib/components/workflow/WorkflowToolbar.svelte`
- [x] T025 [US2] Implement workflow template recommendation: `backend/open_webui/services/workflow/template_recommender.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 2b - Workflow Test Run & Debugging (Priority: P1)

**Goal**: Allow users to test-run workflows in the designer with execution trace

**Independent Test**: Create a workflow, click "Test Run", verify execution trace shows node status and outputs

### Implementation for User Story 2b

- [x] T026 [P] [US2b] Create TestRunPanel component: `src/lib/components/workflow/TestRunPanel.svelte`
- [x] T027 [P] [US2b] Create ExecutionTrace component: `src/lib/components/workflow/ExecutionTrace.svelte`
- [x] T028 [US2b] Implement test-run API endpoint: `backend/open_webui/routers/workflows.py`
- [x] T029 [US2b] Integrate test-run into designer: `src/lib/components/workflow/WorkflowDesigner.svelte`
- [x] T030 [US2b] Implement execution trace visualization: `src/lib/components/workflow/ExecutionTrace.svelte`

**Checkpoint**: User can now test-run workflows and see execution trace

---

## Phase 6: User Story 3 - Comprehensive Node Library & Parameter System (Priority: P1)

**Goal**: Provide rich node library with fixed and custom parameters

**Independent Test**: Build a workflow with 5+ different node types, configure parameters, verify execution

### Implementation for User Story 3

- [x] T031 [P] [US3] Create node type definitions and registry: `src/lib/components/workflow/nodes/index.ts`
- [x] T032 [P] [US3] Create node parameter components (Text, Number, Boolean, Select, File, Reference): `src/lib/components/workflow/parameters/`
- [x] T033 [US3] Create WorkflowNodeSidebar component: `src/lib/components/workflow/WorkflowNodeSidebar.svelte`
- [x] T034 [US3] Implement node configuration panel: `src/lib/components/workflow/NodeConfigPanel.svelte`
- [x] T035 [US3] Implement conditional branching with expressions: `backend/open_webui/services/workflow/conditions.py`
- [x] T036 [US3] Support custom parameter types: `src/lib/components/workflow/parameters/CustomParameter.svelte`

**Checkpoint**: User can build complex workflows with diverse node types and parameters

---

## Phase 7: User Story 4 - Import/Export & Interoperability (Priority: P2)

**Goal**: Support BPMN/XML and JSON import/export

**Independent Test**: Export a workflow to XML, import it back, verify all nodes and edges preserved

### Implementation for User Story 4

- [x] T037 [P] [US4] Implement BPMN export service: `backend/open_webui/services/workflow/bpmn_converter.py`
- [x] T038 [P] [US4] Implement BPMN import service: `backend/open_webui/services/workflow/bpmn_converter.py`
- [x] T039 [US4] Add export buttons to designer toolbar: `src/lib/components/workflow/WorkflowToolbar.svelte`
- [x] T040 [US4] Add import functionality to workflow list: `src/lib/components/workflow/WorkflowList.svelte`
- [x] T041 [US4] Implement JSON export/import: `backend/open_webui/services/workflow/json_converter.py`

**Checkpoint**: User can import/export workflows in XML and JSON formats

---

## Phase 8: User Story 5 - OpenWebUI Chat Integration & Execution (Priority: P2)

**Goal**: Trigger workflows from chat with real-time execution trace

**Independent Test**: Start a chat, select a workflow, verify execution trace and results appear in chat

### Implementation for User Story 5

- [x] T042 [P] [US5] Create chat workflow selector component: `src/lib/components/chat/WorkflowSelector.svelte`
- [x] T043 [P] [US5] Create chat execution trace component: `src/lib/components/chat/WorkflowExecutionTrace.svelte`
- [x] T044 [US5] Integrate workflow selector into chat input: `src/lib/components/chat/ChatInput.svelte`
- [x] T045 [US5] Implement `/workflow-{id}` command handler: `backend/open_webui/routers/workflows.py`
- [x] T046 [US5] Implement chat execution streaming: `backend/open_webui/services/workflow/chat_execution.py`
- [x] T047 [US5] Add pinned workflows quick access: `src/lib/components/chat/WorkflowSelector.svelte`

**Checkpoint**: User can trigger workflows from chat and see execution results

---

## Phase 9: User Story 6 - Unified UI Style (Priority: P3)

**Goal**: Align workflow designer UI with OpenWebUI design system

**Independent Test**: Compare workflow designer with chat page, verify visual consistency

### Implementation for User Story 6

- [x] T048 [P] [US6] Audit and update workflow designer colors to match OpenWebUI tokens: `src/lib/components/workflow/*.svelte`
- [x] T049 [P] [US6] Audit and update typography to match OpenWebUI: `src/lib/components/workflow/*.svelte`
- [x] T050 [US6] Implement dark mode support: `src/lib/components/workflow/*.svelte`
- [x] T051 [US6] Implement responsive layout: `src/lib/components/workflow/*.svelte`
- [x] T052 [US6] Reuse OpenWebUI components (buttons, inputs, modals): `src/lib/components/workflow/*.svelte`

**Checkpoint**: Workflow designer visually matches OpenWebUI design system

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T053 [P] Add workflow versioning support: `backend/open_webui/models/workflows.py`
- [x] T054 [P] Add workflow template system: `backend/open_webui/models/workflows.py`
- [x] T055 Add real-time validation during workflow design: `src/lib/components/workflow/WorkflowDesigner.svelte`
- [x] T056 Add error handling and logging: `backend/open_webui/services/workflow/engine.py`
- [x] T057 Add performance optimization for large workflows: `src/lib/components/workflow/WorkflowCanvas.svelte`
- [x] T058 Add security hardening (input validation, rate limiting): `backend/open_webui/routers/workflows.py`
- [x] T059 Constitution compliance check (Skill-as-Generic-Module)
- [x] T060 Run quickstart.md validation scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 2b (P1)**: Can start after Foundational (Phase 2) - Depends on execution engine from Phase 2
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 5 (P2)**: Can start after Foundational (Phase 2) - Depends on execution engine from Phase 2
- **User Story 6 (P3)**: Can start after Foundational (Phase 2) - UI polish, can be done in parallel

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Create SQLAlchemy models in backend/open_webui/models/workflows.py"
Task: "Create workflow API client in src/lib/apis/workflow/index.ts"
Task: "Create workflow Svelte store in src/lib/stores/workflowStore.ts"

# Then implement UI:
Task: "Create WorkflowList component in src/lib/components/workflow/WorkflowList.svelte"
Task: "Create workflow list page in src/routes/(app)/workflows/+page.svelte"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Global Workflow Access)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (AI Generation) → Test independently → Deploy/Demo
4. Add User Story 2b (Test Run) → Test independently → Deploy/Demo
5. Add User Story 3 (Node Library) → Test independently → Deploy/Demo
6. Add User Story 4 (Import/Export) → Test independently → Deploy/Demo
7. Add User Story 5 (Chat Integration) → Test independently → Deploy/Demo
8. Add User Story 6 (UI Polish) → Test independently → Deploy/Demo
9. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Global Access)
   - Developer B: User Story 2 (AI Generation) + User Story 2b (Test Run)
   - Developer C: User Story 3 (Node Library)
   - Developer D: User Story 4 (Import/Export)
   - Developer E: User Story 5 (Chat Integration)
   - Developer F: User Story 6 (UI Polish)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
