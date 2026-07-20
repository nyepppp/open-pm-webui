# Tasks: Timbal-OpenWebUI Integration

**Input**: Design documents from `/specs/001-timbal-openwebui-integration/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/open_webui/`, `backend/lib/`
- **Frontend**: `src/lib/`, `src/routes/`
- **Tests**: `backend/tests/`, `src/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create Timbal API client directory structure in `backend/lib/timbal/`
- [X] T002 [P] Create Timbal frontend components directory in `src/lib/components/timbal/`
- [X] T003 [P] Create Timbal API routes directory in `backend/open_webui/routers/`
- [X] T004 Add Timbal configuration model in `backend/open_webui/pm/timbal_config.py`
- [X] T005 [P] Create Timbal Svelte store in `src/lib/stores/timbalStore.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement Timbal API client in `backend/lib/timbal/client.py`
- [X] T007 [P] Create Timbal data models in `backend/lib/timbal/models.py`
- [X] T008 [P] Define Timbal tool interfaces in `backend/lib/timbal/tools.py`
- [X] T009 Implement plugin bridge protocol in `backend/lib/timbal/plugin_bridge.py`
- [X] T010 [P] Create Timbal TypeScript types in `src/lib/apis/timbal/types.ts`
- [X] T011 Implement Timbal API client (frontend) in `src/lib/apis/timbal/index.ts`
- [X] T012 Setup error handling and retry logic in `backend/lib/timbal/client.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Timbal Workflow Execution from OpenWebUI (Priority: P1) 🎯 MVP

**Goal**: Enable users to execute Timbal workflows from OpenWebUI via REST API, SSE streaming, and chat commands

**Independent Test**: Configure a Timbal endpoint and trigger a workflow run from the OpenWebUI chat interface or workflow page

### Tests for User Story 1 (OPTIONAL)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Contract test for POST /workflows/{id}/execute in `backend/tests/contract/test_timbal_execution.py`
- [X] T014 [P] [US1] Integration test for SSE streaming in `backend/tests/integration/test_timbal_sse.py`

### Implementation for User Story 1

- [X] T015 [P] [US1] Create TimbalWorkflow model in `backend/lib/timbal/models.py`
- [X] T016 [P] [US1] Create TimbalExecution model in `backend/lib/timbal/models.py`
- [X] T017 [US1] Implement workflow execution service in `backend/lib/timbal/execution_service.py`
- [X] T018 [US1] Implement REST API endpoints for workflow execution in `backend/open_webui/routers/timbal.py`
- [X] T019 [US1] Implement SSE streaming for execution status in `backend/open_webui/routers/timbal.py`
- [X] T020 [US1] Create workflow execution UI component in `src/lib/components/timbal/WorkflowExecution.svelte`
- [X] T021 [US1] Add chat command parser for `/workflow run` in `src/lib/components/chat/MessageInput/`
- [X] T022 [US1] Integrate execution results into chat interface in `src/lib/components/chat/`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - PM Workspace Nodes as Timbal Tools (Priority: P1)

**Goal**: Expose PM workspace capabilities as Timbal-compatible tools for bidirectional data flow

**Independent Test**: Define a Timbal tool that fetches project data and verify it returns correct PM workspace information

### Tests for User Story 2 (OPTIONAL)

- [X] T023 [P] [US2] Contract test for PM tool endpoints in `backend/tests/contract/test_pm_tools.py`
- [X] T024 [P] [US2] Integration test for PM data read/write in `backend/tests/integration/test_pm_tools.py`

### Implementation for User Story 2

- [X] T025 [P] [US2] Create TimbalTool model in `backend/lib/timbal/models.py`
- [X] T026 [US2] Implement PM operation tool definitions in `backend/lib/timbal/tools.py`
- [X] T027 [US2] Implement OpenWebUI skill binding in `backend/lib/timbal/plugin_bridge.py`
- [X] T028 [US2] Implement parameter mapping (auto/manual/template) in `backend/lib/timbal/param_mapper.py`
- [X] T029 [US2] Create tool configuration UI in `src/lib/components/timbal/ToolConfig.svelte`
- [X] T030 [US2] Add PM node types to visual designer in `src/lib/components/timbal/WorkflowNode.svelte`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - OpenWebUI Chat Integration with Timbal (Priority: P2)

**Goal**: Enable natural language workflow invocation from the chat interface

**Independent Test**: Type a natural language command in chat that maps to a Timbal workflow and verify the workflow executes correctly

### Tests for User Story 3 (OPTIONAL)

- [X] T031 [P] [US3] Integration test for chat workflow trigger in `backend/tests/integration/test_chat_integration.py`

### Implementation for User Story 3

- [X] T032 [US3] Implement natural language command parser in `backend/open_webui/routers/timbal.py`
- [X] T033 [US3] Create workflow intent recognition service in `backend/lib/timbal/nlp_service.py`
- [X] T034 [US3] Add interactive project selection in chat in `src/lib/components/chat/`
- [X] T035 [US3] Implement structured output formatting in `src/lib/components/chat/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Visual Workflow Designer for Timbal (Priority: P2)

**Goal**: Provide a visual drag-and-drop interface for creating and editing workflows

**Independent Test**: Create a workflow visually, save it, and execute it successfully

### Tests for User Story 4 (OPTIONAL)

- [X] T036 [P] [US4] Integration test for visual designer CRUD in `backend/tests/integration/test_visual_designer.py`

### Implementation for User Story 4

- [X] T037 [P] [US4] Create SvelteFlow-based workflow designer in `src/lib/components/timbal/WorkflowDesigner.svelte`
- [X] T038 [P] [US4] Implement custom node types (PM Data Source, Get Requirements, Analyze) in `src/lib/components/timbal/WorkflowNode.svelte`
- [X] T039 [US4] Implement node connection validation in `src/lib/components/timbal/WorkflowDesigner.svelte`
- [X] T040 [US4] Add workflow save/load with Git-style versioning in `src/lib/components/timbal/WorkflowDesigner.svelte`
- [X] T041 [US4] Implement version history and diff view in `src/lib/components/timbal/VersionHistory.svelte`

**Checkpoint**: Visual designer is functional and workflows can be created, saved, and executed

---

## Phase 7: User Story 5 - Workflow Management Dashboard (Priority: P3)

**Goal**: Provide a centralized dashboard for viewing and managing all workflows

**Independent Test**: Navigate to the workflows page and verify all CRUD operations work

### Tests for User Story 5 (OPTIONAL)

- [X] T042 [P] [US5] Integration test for dashboard CRUD in `backend/tests/integration/test_dashboard.py`

### Implementation for User Story 5

- [X] T043 [P] [US5] Create workflow list page in `src/routes/(app)/workflows/+page.svelte`
- [X] T044 [P] [US5] Create workflow detail page in `src/routes/(app)/workflows/[workflowId]/+page.svelte`
- [X] T045 [US5] Add execution logs and status display in `src/routes/(app)/workflows/[workflowId]/+page.svelte`
- [X] T046 [US5] Implement workflow enable/disable toggle in `src/routes/(app)/workflows/+page.svelte`

**Checkpoint**: Dashboard is functional and all CRUD operations work

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T047 [P] Documentation updates in `docs/timbal-integration.md`
- [X] T048 Code cleanup and refactoring across `backend/lib/timbal/` and `src/lib/components/timbal/`
- [X] T049 Performance optimization for SSE streaming and workflow execution
- [X] T050 [P] Additional unit tests in `backend/tests/unit/test_timbal_*.py`
- [X] T051 Security hardening for Timbal API endpoints in `backend/open_webui/routers/timbal.py`
- [X] T052 Run quickstart.md validation scenarios

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
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 (execution) and US2 (tools)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 (execution engine)
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (execution) and US4 (designer)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for POST /workflows/{id}/execute in backend/tests/contract/test_timbal_execution.py"
Task: "Integration test for SSE streaming in backend/tests/integration/test_timbal_sse.py"

# Launch all models for User Story 1 together:
Task: "Create TimbalWorkflow model in backend/lib/timbal/models.py"
Task: "Create TimbalExecution model in backend/lib/timbal/models.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Add User Story 5 → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 4
   - Developer E: User Story 5
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
