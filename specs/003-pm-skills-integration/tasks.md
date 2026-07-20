# Tasks: PM Skills Integration

**Input**: Design documents from `/specs/003-pm-skills-integration/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Install Timbal as dependency: `pip install timbal` in `backend/requirements.txt`
- [X] T002 [P] Copy pm-skills repository to `backend/open_webui/pm/skills/pm-skills/`
- [X] T003 Create `backend/open_webui/pm/workflows/` directory for Timbal Workflow definitions
- [X] T004 [P] Configure Timbal model settings in `backend/open_webui/pm/timbal_config.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create `PmSkillsMapping` model in `backend/open_webui/pm/models/pm_skills_mapping.py`
- [X] T006 Create `PmSkillsVersion` model in `backend/open_webui/pm/models/pm_skills_version.py`
- [X] T007 [P] Implement `PmSkillsMapping` CRUD operations in `backend/open_webui/pm/services/pm_skills_mapping_service.py`
- [X] T008 Create `pm_skills_loader.py` in `backend/open_webui/pm/skills/` for loading pm-skills from local files
- [X] T009 Implement skill registry registration in `backend/open_webui/pm/skills/__init__.py`
- [X] T010 Add Timbal Workflow base class in `backend/open_webui/pm/workflows/base_workflow.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Agent 调用 pm-skills 生成结构化产物 (Priority: P1) 🎯 MVP

**Goal**: Agent 调用 pm-skills 方法论（如 `/discover`），生成符合 SkillContract 的结构化产物

**Independent Test**: Trigger `/discover` on a new product idea. Verify the Agent loads skills, produces structured output, and presents it as a draft requiring confirmation.

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `discover_workflow.py` in `backend/open_webui/pm/workflows/` (Timbal Workflow with 4 steps: brainstorm-ideas → identify-assumptions → prioritize-assumptions → brainstorm-experiments)
- [X] T012 [P] [US1] Implement `write_prd_workflow.py` in `backend/open_webui/pm/workflows/` (Timbal Workflow for PRD generation)
- [X] T013 [US1] Create skill wrapper functions in `backend/open_webui/pm/skills/skill_wrappers.py` (wrap pm-skills for Timbal)
- [X] T014 [US1] Implement Agent integration in `backend/open_webui/pm/agent/pm_skills_agent.py` (Agent invokes pm-skills via Timbal Workflow)
- [X] T015 [US1] Add output validation against `outputContract` in `backend/open_webui/pm/services/output_validator.py`
- [X] T016 [US1] Implement confirmation gate in `backend/open_webui/pm/services/confirmation_service.py`
- [X] T017 [US1] Persist confirmed output to `ModuleEntry` in `backend/open_webui/pm/services/module_entry_service.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 用户显式调用 pm-skills 命令 (Priority: P1)

**Goal**: 用户通过 `/pm-<id>` 命令显式调用 pm-skills，获得确定性输出

**Independent Test**: Type `/pm-write-prd` in agent chat. Verify deterministic invocation and structured draft output.

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement `/pm-<id>` command parser in `backend/open_webui/pm/intent.py`
- [X] T019 [US2] Create command resolution service in `backend/open_webui/pm/services/command_resolver.py`
- [X] T020 [US2] Implement explicit invocation handler in `backend/open_webui/pm/skills/explicit_invocation.py`
- [ ] T021 [US2] Add skill palette UI component in `src/lib/components/pm/SkillPanel.svelte`
- [ ] T022 [US2] Implement frontend command input in `src/lib/components/pm/CommandInput.svelte`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Agent 按需加载 pm-skills (Priority: P2)

**Goal**: Agent 根据对话上下文自动加载相关 pm-skills 方法论

**Independent Test**: Ask Agent "How should we price our new AI feature?" Verify autonomous skill loading.

### Implementation for User Story 3

- [X] T023 [P] [US3] Implement context analyzer in `backend/open_webui/pm/services/context_analyzer.py`
- [X] T024 [US3] Create skill relevance scorer in `backend/open_webui/pm/services/skill_relevance.py`
- [X] T025 [US3] Implement autonomous skill loader in `backend/open_webui/pm/agent/autonomous_skill_loader.py`
- [X] T026 [US3] Add skill registry summary injection in `backend/open_webui/pm/pipelines/skill_registry_injection.py`

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - 管理员配置映射关系 (Priority: P2)

**Goal**: 管理员配置 pm-skills 与 SkillContract 的映射关系

**Independent Test**: Add new pm-skills mapping via admin UI. Verify it appears in registry.

### Implementation for User Story 4

- [ ] T027 [P] [US4] Create admin UI for mapping configuration in `src/lib/components/pm/AdminMappingConfig.svelte`
- [X] T028 [US4] Implement mapping CRUD API in `backend/open_webui/pm/api/mapping_api.py`
- [X] T029 [US4] Add mapping validation in `backend/open_webui/pm/services/mapping_validator.py`
- [X] T030 [US4] Implement version pinning in `backend/open_webui/pm/services/version_service.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Add error handling and fallback for Timbal Workflow failures
- [X] T032 [P] Implement logging and observability for pm-skills execution
- [X] T033 Add performance monitoring (Tool calls ≤ 3s, skill loading ≤ 1s)
- [X] T034 [P] Create documentation for pm-skills integration
- [X] T035 [P] Add unit tests for Timbal Workflow definitions
- [ ] T036 Constitution compliance check (Skill-as-Generic-Module: verify new agent capabilities are SkillContract or pm_* Tool)
- [ ] T037 Run quickstart.md validation

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
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1/US2/US3 but should be independently testable

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
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 4
3. Stories complete and integrate independently
