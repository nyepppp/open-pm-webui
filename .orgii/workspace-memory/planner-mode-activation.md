---
name: PM Module Implementation Plan Approved
description: 5-phase PM module implementation plan approved 2026-07-03; 7 tasks created and assigned to sde-implementer. Task 0c7a4fea (traceability DB/API) completed by sde-planner on 2026-07-03.
type: workspace
---

**Status:** All 7 tasks marked complete (2026-07-03T00:19Z), but sde-reviewer code review (task 996b752c, 2026-07-03T00:25Z) found **4 P0 blocking bugs — rework required before functional testing can begin**. All 5 rework tasks completed by sde-implementer (2026-07-03T00:35Z).

**Review findings (2026-07-03):**
P0 (backend won't start / core endpoints broken / security):
1. `PMEntryVersion.metadata` + `PMEntity.metadata` use SQLAlchemy reserved attribute name → server import raises `InvalidRequestError: Attribute name 'metadata' is reserved`. Must rename column + Pydantic field + all call sites. Repo convention uses `info` (users.py) or `vmetadata` (pgvector).
2. `/traceability/validate` at `routers/pm.py:1147` calls `select(PMRelation)` without importing either symbol → NameError on hit.
3. `/versions/compare` is shadowed by earlier `/versions/{version_id}` route registration; `compare_entry_versions` is also defined twice (L329 + L893) with inconsistent param names. Neither compare endpoint reachable.
4. All entry / entity / relation / version endpoints skip ownership checks → cross-user read/write/delete possible.

Medium: Pydantic `metadata` field will serialize the class-level MetaData object under `from_attributes=True`. `_call_llm` sends empty `model` string. `create_project_version_snapshot` has no idempotency. Fallback version-number `f'v{int(time.time())}'` collides on concurrent inserts.

Frontend: `+page.svelte` imports `moduleFields.ts` helpers but still drives rendering from a local `moduleConfig` — two inconsistent configs (`meeting` local=rich vs mixed; `prototype` local=table vs mixed; local uses invalid `'competitor'` editorType). `agentTools.ts` uses `||` where `??` is needed for empty-string handling. `apis/pm/index.ts` exports generic `getOne/create/update/remove` helpers with no callers.

Passing: `PMEntity`/`PMRelation` schema, `get_trace_chain` recursion+cycle handling, diff dual-channel design, skill registry frontend/backend alignment.

**Task Completion Summary:**
| ID | Task | Assignee | Status |
|----|------|----------|--------|
| `0c7a4fea` | 搭建溯源数据库表和API | sde-planner | ✅ completed |
| `0ecedfed` | 实现模块差异化编辑器 | sde-implementer | ✅ completed |
| `eeb8cacb` | 打通版本功能前后端 | sde-planner | ✅ completed |
| `9bdad485` | 实现Agent通用对接模块 | sde-planner | ✅ completed |
| `1f58b41c` | 打通项目版本与文件版本关联 | sde-implementer | ✅ completed |
| `5d97686a` | 实现溯源版本流转判定 | sde-implementer | ✅ completed |
| `018fe0da` | 完善所有模块基础信息对齐PRD | sde-implementer | ✅ completed |

**Plan Source:** Planner (sde-planner) produced 5-phase plan (pm_f295fc71); coordinator approved and assigned tasks. **Plan resubmitted as pm_4927f5ec on 2026-07-03** with updated 5-phase breakdown and 12 key files identified.

**Assigned Tasks (all to sde-implementer):**
| ID | Task | Status |
|----|------|--------|
| `0c7a4fea` | 搭建溯源数据库表和API | **completed** by sde-planner |
| `0ecedfed` | 实现模块差异化编辑器 | **completed** by sde-implementer |
| `eeb8cacb` | 打通版本功能前后端 | **completed** by sde-planner |
| `9bdad485` | 实现Agent通用对接模块 | **completed** by sde-planner |
| `1f58b41c` | 打通项目版本与文件版本关联 | **completed** by sde-implementer |
| `5d97686a` | 实现溯源版本流转判定 | **completed** by sde-implementer |
| `018fe0da` | 完善所有模块基础信息对齐PRD | **completed** by sde-implementer |

**Next Phase:** Code review (sde-reviewer) and functional testing (sde-tester) in progress. All 4 P0 bugs and 1 frontend type issue fixed by sde-implementer (2026-07-03T00:35Z). sde-tester functional testing is now unblocked. 5 medium issues remain in backlog (empty model string, snapshot idempotency, version collision, frontend config duality, `agentTools.ts` `||` vs `??`).

**5-Phase Plan Summary:**
1. **Phase 1 — Module Differentiation + Data Layer**: Extend 13 modules with PRD-aligned differentiated fields and editors
2. **Phase 2 — Versioning Complete Loop**: Entry-level snapshots, version panel, diff viewer, rollback UI, project-file version linkage
3. **Phase 3 — Traceability (Relationship Network)**: entities/relations tables, bidirectional tracing, impact analysis, version-aware relationships
4. **Phase 4 — Agent Deep Integration**: Reuse OpenWebUI Agent or build generic wrapper; implement 8 skills (PRD generation, requirement analysis, competitor research, prototype check, parameter extraction, testcase generation, version comparison, relationship suggestion)
5. **Phase 5 — Cross-Module Connectivity**: Module inter-jumping, dashboard aggregation, global search, import/export, activity feed

**Execution Priority:**
- Phase 1 core modules (PRD, parameter, testcase, competitor, risk) before secondary modules
- Phase 2 version APIs before Phase 3 traceability (traceability depends on version data)
- Phase 4 Agent integration can run in parallel after Phase 1 completes
- Phase 5 cross-module connectivity must wait for Phase 1-3

**Completed Work (Task 0c7a4fea):**
- `PMEntity` and `PMRelation` SQLAlchemy models added to `backend/open_webui/models/pm.py`
- `PMEntities` and `PMRelations` CRUD classes added (insert, get, delete, impact analysis, trace chain)
- Router endpoints added in `backend/open_webui/routers/pm.py`:
  - `GET/POST /projects/{project_id}/entities` — entity list/create
  - `DELETE /entities/{entity_id}` — delete entity
  - `GET/POST /projects/{project_id}/relations` — relation list/create
  - `DELETE /relations/{relation_id}` — delete relation
  - `GET /entities/{entity_id}/relations` — entity relations
  - `GET /projects/{project_id}/traceability/impact` — impact analysis (upstream/downstream)
  - `GET /projects/{project_id}/traceability/chain` — trace chain with recursive depth control
  - `GET /projects/{project_id}/traceability/validate` — version flow reasonableness validation (Task 5d97686a)

**Completed Work (Task 0ecedfed):**
- `src/lib/components/pm/moduleFields.ts` extended with full field configs for 13 modules
- `moduleFieldRegistry`, `moduleEditorConfig`, `getModuleFields()`, `getModuleEditorConfig()` added
- 4 editor types supported: rich, form, mixed, mindmap, table
- `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` imports new field config system

**Completed Work (Task eeb8cacb):**
- Backend: Added `GET /projects/{project_id}/entries/{entry_id}/versions/{version_id_a}/diff/{version_id_b}` — text diff using Python `difflib`
- Backend: Added `GET /projects/{project_id}/entries/{entry_id}/versions/compare` — structured diff (content + metadata)
- Frontend components already existed:
  - `PMVersionHistoryDropdown.svelte` — version list + switch
  - `PMVersionComparePanel.svelte` — LCS-based diff viewer with restore
  - `PMVersionRollbackDialog.svelte` — rollback confirmation dialog
  - `PMVersionBranchDialog.svelte` — branch creation
  - `PMVersionMergePanel.svelte` — merge panel
- Frontend API `src/lib/apis/pm/version.ts` already had `compareEntryVersions()` calling `/versions/compare`
- Integration: Version controls in `+page.svelte` toolbar (history dropdown, compare button, branch button, merge button)
- Project-version ↔ entry-version linkage: `/projects/{pid}/versions/{vid}/snapshot` and `/projects/{pid}/versions/{vid}/entries` (Task 1f58b41c)

**Completed Work (Task 9bdad485):**
- New file `src/lib/apis/pm/agentTools.ts` — Agent tool registry, skill config, execution engine
- Backend: `/agent/tools/*` 5 tool APIs (create_entry, update_entry, create_relation, list_entries, get_entry)
- 9 skill configurations: PRD generation, requirement analysis, competitor research, prototype check, parameter extraction, testcase generation, version comparison, relation suggestion, workflow suggestion

**Updated Plan (pm_4927f5ec, 2026-07-03):**
- Phase 1: Module base-info alignment with PRD (1-2 days) — `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`, `src/lib/apis/pm/types.ts`
- Phase 2: Version system打通 — project-version ↔ entry-version ↔ base-info linkage; `backend/open_webui/models/pm.py`, `PMVersionComparePanel.svelte`
- Phase 3: Traceability完善 — auto entity/relation creation, version flow tracking, reasonableness validation rules
- Phase 4: Agent对接OpenWebUI — reuse native Agent/tool system, build `PMTool<TInput,TOutput>` generic module, register 6 tools (EntryCreate/Update/Query, VersionCreate, RelationCreate, TraceabilityAnalyze)
- Phase 5: Workflow integration — workflow board, version management page, traceability page, preset workflow templates

**Key gaps identified (from code audit):**
- `src/routes/(app)/pm/[projectId]/workflow/+page.svelte` — empty, needs workflow board
- `src/routes/(app)/pm/[projectId]/versions/+page.svelte` — empty, needs version management
- `src/routes/(app)/pm/[projectId]/traceability/+page.svelte` — empty, needs full-project relation graph
- `backend/open_webui/pm/tools/` — does not exist, needs generic tool module
- `backend/open_webui/pm/workflows/` — does not exist, needs workflow templates
- `PMTraceabilityGraph.svelte` — static mock data, needs real `pm_relation` data
- `PMAgentChatPanel.svelte` — standalone implementation, needs OpenWebUI native integration
- `pm_entry_version` table lacks `project_version_id` foreign key

**Why:**
User granted highest execution approval for PM workspace deep integration. The 6-goal mandate covers: (1) module differentiation, (2) versioning, (3) traceability, (4) version linkage, (5) Agent integration, (6) overall completion. User specifically referenced OpenWebUI docs (https://docs.openwebui.com/) and deepseek wiki for Agent/tool integration patterns.

**How to apply:**
When working on PM module tasks, check task board for current status. sde-implementer is responsible for execution; coordinator handles task assignment and status tracking. Tasks must be started in order: Phase 1 tasks (0c7a4fea, 0ecedfed) can run in parallel, then Phase 2 (eeb8cacb), then Phase 3+ (1f58b41c, 5d97686a, 018fe0da). Task 0c7a4fea is done — no additional traceability DB work needed. For Agent work (Phase 4), prioritize reusing OpenWebUI native functions/tools/skills system over standalone implementation — consult OpenWebUI docs to determine best integration point.