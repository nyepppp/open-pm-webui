# Tasks: SPEC Module Bug Fixes

**Input**: Design documents from `/specs/001-spec-module-bugfix/`

**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Not requested — this is a bug fix feature with manual browser validation per quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify project context and ensure all prerequisites are in place

- [x] T001 Verify `getEntries` API supports all target module types (requirement, parameter, module, feature) in `src/lib/apis/pm/index.ts`
- [x] T002 Verify `updateEntry` API can persist annotation arrays in entry data in `src/lib/apis/pm/index.ts`
- [x] T003 [P] Confirm PMRelationPicker, PMSpecGlossaryPanel, PMAnnotationPanel, and PMRichEditor component files exist at expected paths

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Ensure the SPEC editor page loads related entries correctly before any user story work

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Update `loadRelatedEntries()` in `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` to also fetch module and feature entries when `moduleType === 'spec'`
- [x] T005 Verify requirementEntries, parameterEntries, and any new entry arrays are populated before rendering relation selectors in `+page.svelte`
- [x] T006 Ensure `PMRichEditor` exposes its TipTap `editor` instance to parent via callback or bindable prop

**Checkpoint**: Foundation ready — SPEC editor page loads with real data available for all relation types

---

## Phase 3: User Story 1 — Associate Real Project Entities in SPEC Module (Priority: P1) 🎯 MVP

**Goal**: Replace mock data in PMRelationPicker with real project entity data so users can select and associate requirements, modules, features, and parameters with a SPEC.

**Independent Test**: Open a SPEC entry. The "关联需求", "关联模块", "关联功能", and "关联参数" dropdowns should show real entries from the project. Selecting an entry persists after save and reload.

### Implementation for User Story 1

- [x] T007 [P] [US1] Replace mock data in `PMRelationPicker.loadItems()` with `getEntries(token, projectId, targetModuleType)` call in `src/lib/components/pm/PMRelationPicker.svelte`
- [x] T008 [P] [US1] Add loading and error states to `PMRelationPicker` in `src/lib/components/pm/PMRelationPicker.svelte`
- [x] T009 [US1] Wire `PMRelationPicker` into SPEC editor for "关联需求" selector in `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
- [x] T010 [US1] Wire `PMRelationPicker` into SPEC editor for "关联模块" selector in `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
- [x] T011 [US1] Wire `PMRelationPicker` into SPEC editor for "关联功能" selector in `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
- [x] T012 [US1] Wire `PMRelationPicker` into SPEC editor for "关联参数" selector in `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
- [x] T013 [US1] Persist selected relations to `specRelatedRequirements`, `specRelatedModules`, `specRelatedFeatures`, `specRelatedParameters` state in `+page.svelte`
- [x] T014 [US1] Ensure relations are saved via `updateEntry` when SPEC document is saved in `+page.svelte`
- [x] T015 [US1] Display selected relations in SPEC list view (card metadata) in `+page.svelte`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 — Functional Insert/Add Actions in SPEC Module (Priority: P1)

**Goal**: Fix the "术语参考" (terminology reference) insert action so it responds and inserts content into the editor.

**Independent Test**: Open a SPEC entry with "前端原型" category. Click "术语参考" panel → "插入" on any term. The term definition should appear in the editor at the cursor position.

### Implementation for User Story 2

- [x] T016 [P] [US2] Add `onEditorReady` callback or `bind:this` to `PMRichEditor` to expose TipTap `editor` instance in `src/lib/components/pm/PMRichEditor.svelte`
- [x] T017 [US2] Capture `editor` instance in `+page.svelte` when `PMRichEditor` mounts
- [x] T018 [US2] Pass `editor` prop to `PMSpecGlossaryPanel` in SPEC editor layout in `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
- [x] T019 [US2] Verify `insertTerm()` in `PMSpecGlossaryPanel` receives valid editor and inserts content at cursor in `src/lib/components/pm/PMSpecGlossaryPanel.svelte`
- [x] T020 [US2] Handle edge case where editor is not yet initialized (disable insert button or show loading state) in `src/lib/components/pm/PMSpecGlossaryPanel.svelte`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 — Synchronized Annotations with Working AI Edit (Priority: P1)

**Goal**: Fix annotation data persistence and the AI Modify button so annotations sync across reloads and AI editing workflow triggers correctly.

**Independent Test**: Open a SPEC entry, add an annotation, save, reload — annotation should persist. Click "AI修改" on an annotation — an AI workflow should initiate (e.g., agent chat panel opens with annotation content).

### Implementation for User Story 3

- [x] T021 [P] [US3] Update `onAnnotationsChange` in `+page.svelte` to persist annotations via `updateEntry()` instead of only local state in `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
- [x] T022 [US3] Ensure annotation array in `editingEntry.data.annotations` is correctly serialized and sent to API in `+page.svelte`
- [x] T023 [US3] Load annotations from `editingEntry.data.annotations` when opening SPEC editor in `+page.svelte`
- [x] T024 [US3] Replace `prompt()`-based `handleAiModify` in `PMRichEditor` with AI workflow initiation (open agent chat panel with annotation content) in `src/lib/components/pm/PMRichEditor.svelte`
- [x] T025 [US3] Implement graceful fallback when AI service is unavailable (show toast message per Constitution Principle I) in `src/lib/components/pm/PMRichEditor.svelte`
- [x] T026 [US3] Ensure annotation count in `PMAnnotationPanel` header updates reactively after add/remove in `src/lib/components/pm/PMAnnotationPanel.svelte`
- [x] T027 [US3] Verify annotation panel displays correct author, timestamp, and content after reload in `src/lib/components/pm/PMAnnotationPanel.svelte`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T028 [P] Verify no mock/static data ("示例条目", "123测试测试测试") remains in any SPEC module field
- [x] T029 [P] Add empty state handling when no entries exist for a relation type (show "无数据" instead of leaving selector empty)
- [ ] T030 [P] Run quickstart.md validation scenarios and verify all 4 scenarios pass
- [x] T031 Update `CLAUDE.md` agent context reference if needed (already updated in plan phase)
- [x] T032 Code review: ensure no hardcoded strings, all user-facing text uses existing i18n patterns

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (US1 → US2 → US3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — Independent of US1, but both can run in parallel
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) — Independent of US1/US2, but all three can run in parallel

### Within Each User Story

- Core implementation before integration
- Story complete before moving to next

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all three user stories can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all independent tasks for User Story 1 together:
Task: "Replace mock data in PMRelationPicker.loadItems() with getEntries() in src/lib/components/pm/PMRelationPicker.svelte"
Task: "Add loading and error states to PMRelationPicker in src/lib/components/pm/PMRelationPicker.svelte"

# Then wire selectors:
Task: "Wire PMRelationPicker into SPEC editor for '关联需求' selector in +page.svelte"
Task: "Wire PMRelationPicker into SPEC editor for '关联模块' selector in +page.svelte"
Task: "Wire PMRelationPicker into SPEC editor for '关联功能' selector in +page.svelte"
Task: "Wire PMRelationPicker into SPEC editor for '关联参数' selector in +page.svelte"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (real data association)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (real data association)
   - Developer B: User Story 2 (glossary insert)
   - Developer C: User Story 3 (annotation sync + AI modify)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
