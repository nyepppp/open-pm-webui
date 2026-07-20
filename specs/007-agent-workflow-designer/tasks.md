# Tasks: Agent Workflow Designer & Architecture Fix

**Input**: Design documents from `/specs/007-agent-workflow-designer/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure) ✅ COMPLETE

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create workflow models (Workflow, WorkflowNode, WorkflowEdge, WorkflowExecution) in `backend/open_webui/pm/models/workflow.py`
- [X] T002 [P] Create session binding model (SessionBinding) in `backend/open_webui/pm/models/session_binding.py`
- [X] T003 [P] Create traceability model (TraceabilityLink) in `backend/open_webui/pm/models/traceability.py`
- [X] T004 Run database migrations for new models in `backend/open_webui/pm/migrations/`
- [X] T005 [P] Create workflow service skeleton in `backend/open_webui/pm/services/workflow_service.py`
- [X] T006 [P] Create session binding service skeleton in `backend/open_webui/pm/services/session_binding_service.py`
- [X] T007 Create workflow API router in `backend/open_webui/pm/api/workflows.py`
- [X] T008 Create session binding API router in `backend/open_webui/pm/api/sessions.py`

---

## Phase 2: Foundational (Blocking Prerequisites) ✅ COMPLETE

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T009 Implement Workflow model with validation (unique name, single start, at least one end) in `backend/open_webui/pm/models/workflow.py`
- [X] T010 [P] Implement WorkflowNode model with type enum and custom script support in `backend/open_webui/pm/models/workflow.py`
- [X] T011 [P] Implement WorkflowEdge model with data mapping rules validation in `backend/open_webui/pm/models/workflow.py`
- [X] T012 Implement WorkflowExecution model with status transitions in `backend/open_webui/pm/models/workflow.py`
- [X] T013 [P] Implement SessionBinding model with active binding constraint in `backend/open_webui/pm/models/session_binding.py`
- [X] T014 Implement TraceabilityLink model with confidence score validation in `backend/open_webui/pm/models/traceability.py`
- [X] T015 Create async workflow execution engine in `backend/open_webui/pm/services/workflow_engine.py`
- [X] T016 Implement workflow validation service (circular dependency check, orphaned nodes) in `backend/open_webui/pm/services/workflow_service.py`
- [X] T017 Create shared workflow types/enums in `backend/open_webui/pm/types/workflow.py`
- [X] T018 Add workflow API endpoints (CRUD) in `backend/open_webui/pm/api/workflows.py`
- [X] T019 Add session binding API endpoints in `backend/open_webui/pm/api/sessions.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Visual Workflow Designer (Priority: P1) 🎯 MVP ✅ COMPLETE

**Goal**: Build a visual workflow designer with draggable nodes, connections, and data transformation configuration

**Independent Test**: Create a workflow with 3+ connected nodes, save it, and verify data flows correctly through the pipeline

### Implementation for User Story 1

- [X] T020 [P] [US1] Create WorkflowDesigner Svelte component in `src/lib/components/pm/workflow/WorkflowDesigner.svelte`
- [X] T021 [P] [US1] Create WorkflowNode Svelte component (draggable, configurable) in `src/lib/components/pm/workflow/WorkflowNode.svelte`
- [X] T022 [P] [US1] Create WorkflowEdge Svelte component (connection lines) in `src/lib/components/pm/workflow/WorkflowEdge.svelte`
- [X] T023 [US1] Implement node drag-and-drop logic in `src/lib/components/pm/workflow/WorkflowDesigner.svelte`
- [X] T024 [US1] Implement edge creation (connect two nodes) in `src/lib/components/pm/workflow/WorkflowDesigner.svelte`
- [X] T025 [US1] Create NodeConfigPanel component for data transformation rules in `src/lib/components/pm/workflow/NodeConfigPanel.svelte`
- [X] T026 [US1] Implement node configuration UI (type selection, config form) in `src/lib/components/pm/workflow/NodeConfigPanel.svelte`
- [X] T027 [US1] Add workflow save/load API integration in `src/lib/components/pm/workflow/WorkflowDesigner.svelte`
- [X] T028 [US1] Implement workflow execution trigger and status display in `src/lib/components/pm/workflow/WorkflowDesigner.svelte`
- [X] T029 [US1] Add workflow designer route/page in `src/routes/pm/workflows/+page.svelte`
- [X] T030 [US1] Implement workflow execution endpoint (POST /api/pm/workflows/{id}/execute) in `backend/open_webui/pm/api/workflows.py`
- [X] T031 [US1] Implement workflow execution status endpoint (GET /api/pm/workflows/{id}/executions/{exec_id}) in `backend/open_webui/pm/api/workflows.py`
- [X] T032 [US1] Add execution history display in workflow designer in `src/lib/components/pm/workflow/WorkflowExecutionHistory.svelte`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - PM Workspace Session Persistence (Priority: P1) ✅ COMPLETE

**Goal**: Enable chat sessions to bind to PM workspaces, allowing agents to read workspace data contextually

**Independent Test**: Bind a session to a PM workspace and ask the agent to summarize documents from that workspace

### Implementation for User Story 2

- [X] T033 [P] [US2] Create WorkspaceSelector Svelte component in `src/lib/components/pm/session/WorkspaceSelector.svelte`
- [X] T034 [US2] Add workspace dropdown to chat input area in `src/lib/components/chat/ChatInput.svelte`
- [X] T035 [US2] Implement session binding API call in `src/lib/components/pm/session/WorkspaceSelector.svelte`
- [X] T036 [US2] Implement session workspace context injection in `backend/open_webui/pm/services/session_binding_service.py`
- [X] T037 [US2] Add workspace data access to agent pipeline in `backend/open_webui/pm/pipelines/workspace_context.py`
- [X] T038 [US2] Implement workspace switching mid-session in `src/lib/components/pm/session/WorkspaceSelector.svelte`
- [X] T039 [US2] Add session unbinding functionality in `src/lib/components/pm/session/WorkspaceSelector.svelte`
- [X] T040 [US2] Update agent context with workspace data on binding in `backend/open_webui/pm/services/session_binding_service.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Agent Capability: Workspace Data Access (Priority: P2) ✅ COMPLETE

**Goal**: Enable agent to actively read from any PM workspace module and import data to target modules

**Independent Test**: Instruct the agent to read requirements and generate test cases in another module

### Implementation for User Story 3

- [X] T041 [P] [US3] Create pm_read_module tool in `backend/open_webui/pm/tools/pm_tools.py`
- [X] T042 [P] [US3] Create pm_write_module tool in `backend/open_webui/pm/tools/pm_tools.py`
- [X] T043 [US3] Implement human confirmation modal for dangerous operations in `src/lib/components/pm/agent/ConfirmationModal.svelte`
- [X] T044 [US3] Add confirmation logic to pm_write_module tool in `backend/open_webui/pm/tools/pm_tools.py`
- [X] T045 [US3] Implement cross-module data read service in `backend/open_webui/pm/services/module_data_service.py`
- [X] T046 [US3] Implement cross-module data write service with confirmation in `backend/open_webui/pm/services/module_data_service.py`
- [X] T047 [US3] Add agent skill for "generate test cases from requirements" in `backend/open_webui/pm/skills/pm_generate_test_cases.py`
- [X] T048 [US3] Add agent skill for "extract parameters from PRD" in `backend/open_webui/pm/skills/pm_generate_test_cases.py`
- [X] T049 [US3] Register new skills in skill registry in `backend/open_webui/pm/skills/registry.py`

**Checkpoint**: User Stories 1, 2, AND 3 should now be independently functional

---

## Phase 6: User Story 4 - PM Module Integration: Documents/Skills (Priority: P2) ✅ COMPLETE

**Goal**: Support fixed workflows (Idea→PRD, Requirements→Test Cases) with full traceability

**Independent Test**: Run a workflow from ideation to PRD generation and verify traceability links

### Implementation for User Story 4

- [X] T050 [P] [US4] Create fixed workflow templates (Idea→PRD, Requirements→Test Cases) in `backend/open_webui/pm/workflows/templates/fixed_workflows.py`
- [X] T051 [US4] Implement traceability link generation service in `backend/open_webui/pm/services/traceability_service.py`
- [X] T052 [US4] Add traceability graph visualization component in `src/lib/components/pm/workflow/TraceabilityGraph.svelte`
- [X] T053 [US4] Implement skill invocation via `/pm-<id>` command in `backend/open_webui/pm/api/skills.py`
- [X] T054 [US4] Add skill command parser in chat input in `src/lib/components/chat/ChatInput.svelte`
- [X] T055 [US4] Create traceability link API endpoints in `backend/open_webui/pm/api/traceability.py`
- [X] T056 [US4] Add traceability view to workflow designer in `src/lib/components/pm/workflow/WorkflowDesigner.svelte`

**Checkpoint**: All user stories 1-4 should now be independently functional

---

## Phase 7: User Story 5 - Fix Product Architecture Diagram (Priority: P3) ✅ COMPLETE

**Goal**: Fix existing architecture diagram rendering and interaction issues

**Independent Test**: Navigate to architecture diagram page and verify all nodes display and are clickable

### Implementation for User Story 5

- [X] T057 [P] [US5] Fix architecture diagram rendering errors in `src/lib/components/pm/architecture/ArchitectureDiagram.svelte`
- [X] T058 [US5] Fix node click interaction in `src/lib/components/pm/architecture/ArchitectureDiagram.svelte`
- [X] T059 [US5] Fix connection hover tooltip in `src/lib/components/pm/architecture/ArchitectureDiagram.svelte`
- [X] T060 [US5] Add skill definition display on skill node click in `src/lib/components/pm/architecture/ArchitectureDiagram.svelte`
- [X] T061 [US5] Verify architecture diagram loads without errors in browser console

**Checkpoint**: All user stories should now be independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns ✅ COMPLETE

**Purpose**: Improvements that affect multiple user stories

- [X] T062 [P] Add error handling and logging across all workflow services in `backend/open_webui/pm/services/`
- [X] T063 [P] Add input validation and sanitization to all API endpoints in `backend/open_webui/pm/api/`
- [X] T064 Add rate limiting to workflow execution endpoints in `backend/open_webui/pm/api/workflows.py`
- [X] T065 [P] Update PM workspace navigation to include workflow designer link in `backend/open_webui/routers/pm.py`
- [X] T066 Add workflow designer access control (check user permissions) in `backend/open_webui/pm/services/workflow_service.py`
- [X] T067 [P] Documentation updates in `docs/pm/workflows.md`
- [X] T068 Constitution compliance check: verify all agent capabilities are SkillContract or pm_* Tool in `backend/open_webui/pm/skills/`
- [X] T069 Run quickstart.md validation scenarios
- [X] T070 [P] Performance optimization: add database indexes for workflow queries in `backend/open_webui/pm/models/workflow.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately ✅
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories ✅
- **User Stories (Phase 3+)**: All depend on Foundational phase completion ✅
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete ✅

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories ✅
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable ✅
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on US2 for session binding context ✅
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for workflow designer ✅
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Independent, bug fixes only ✅

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel ✅
- All Foundational tasks marked [P] can run in parallel (within Phase 2) ✅
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows) ✅
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Summary

**All Phases Complete!**

| Phase | Status | Tasks | Description |
|-------|--------|-------|-------------|
| Phase 1 | ✅ | T001-T008 | Setup - Models and basic structure |
| Phase 2 | ✅ | T009-T019 | Foundational - Core infrastructure |
| Phase 3 | ✅ | T020-T032 | US1 - Visual Workflow Designer |
| Phase 4 | ✅ | T033-T040 | US2 - Session Persistence |
| Phase 5 | ✅ | T041-T049 | US3 - Agent Workspace Data Access |
| Phase 6 | ✅ | T050-T056 | US4 - Fixed Workflows & Traceability |
| Phase 7 | ✅ | T057-T061 | US5 - Fix Architecture Diagram |
| Phase 8 | ✅ | T062-T070 | Polish & Cross-Cutting Concerns |

**Total**: 70/70 tasks completed

### New Files Created

**Backend:**
- `backend/open_webui/pm/tools/pm_tools.py` - PM read/write tools
- `backend/open_webui/pm/services/module_data_service.py` - Cross-module data service
- `backend/open_webui/pm/services/traceability_service.py` - Traceability link management
- `backend/open_webui/pm/skills/pm_generate_test_cases.py` - Test case generation skill
- `backend/open_webui/pm/skills/registry.py` - Skill registry
- `backend/open_webui/pm/workflows/templates/fixed_workflows.py` - Fixed workflow templates
- `backend/open_webui/pm/api/skills.py` - Skill invocation API
- `backend/open_webui/pm/api/traceability.py` - Traceability API

**Frontend:**
- `src/lib/components/pm/agent/ConfirmationModal.svelte` - Agent operation confirmation
- `src/lib/components/pm/workflow/TraceabilityGraph.svelte` - Traceability visualization
- `src/lib/components/pm/architecture/ArchitectureDiagram.svelte` - Fixed architecture diagram

**Modified:**
- `backend/open_webui/routers/pm.py` - Added sub-router includes for workflows, sessions, skills, traceability
