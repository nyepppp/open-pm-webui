---
name: PM v4 bug batch — verdict FAILED on re-verification
description: PM v4 bugfix batch: sde-implementer claimed 11 tasks done, but sde-tester re-verification 2026-07-03T01:05Z found NEW P0 (Alembic Multiple Heads) + 133 frontend errors remain + smoke tests all crash.

**Status as of 2026-07-03T01:15Z:**
- P0 Alembic Multiple Heads: FIXED - down_revision corrected to actual head 461111b60977
- P1 +page.svelte syntax errors: STILL BROKEN - if-else chain at lines 1890-1912 unclosed
- P1 API contract sync: STILL BROKEN - entry_metadata/entity_metadata not synced to frontend types.ts
- P1 PMVersionComparePanel.svelte: NEW ISSUE - diffLines variable undefined at lines 68,186,238,240
- P1 Smoke tests: STILL BROKEN - missing conftest.py, fixtures undefined, assertions accept HTTP 500
- P2 SvelteFlow component types: STILL BROKEN - nodes/edges type mismatch with @xyflow/svelte v1 API

**Root causes:**
- sde-implementer claims "done" without verifying fixes actually work
- Frontend type definitions (types.ts) not updated when backend renames fields
- Svelte components have syntax errors that prevent compilation
- Test files lack required pytest fixtures and have invalid assertions
type: workspace
---

**Status (2026-07-03T01:05Z re-verification): FAILED — cannot ship.**

**Update (2026-07-03T01:10Z): P0-new1 (Alembic Multiple Heads) FIXED by sde-implementer.**
- `f2e3d4c5b6a7_add_pm_tables.py` down_revision changed from `'f1e2d3c4b5a6'` to `'461111b60977'`.
- Verified by inspecting migration file content.
- Remaining: 4 of 5 tasks still pending.

**Genuinely fixed (verified by re-import + code inspection):**
- P0: SQLAlchemy `metadata` → `entry_metadata` / `entity_metadata` (models/pm.py:72, 124). `import open_webui.main` now succeeds; 45 PM routes register.
- P1: `select` + `PMRelation` imports added (routers/pm.py:20-24).
- P1: Duplicate `compare_entry_versions` de-duplicated (only one left at routers/pm.py:367).
- P0-new1: Alembic down_revision corrected to point to actual head `461111b60977`.

**NEW P0 blocker (introduced by the fix, not caught before):**
- `backend/open_webui/migrations/versions/f2e3d4c5b6a7_add_pm_tables.py` sets `down_revision = 'f1e2d3c4b5a6'` (access grant table) but the real Alembic head is `461111b60977`. Two heads → `alembic upgrade head` raises `MultipleHeads` on every startup.
- Local dev only survives because `main.py:675 Base.metadata.create_all` runs as fallback. Production/prod-migration paths break.
- Fix: `alembic merge -m "merge pm branch" 461111b60977 f2e3d4c5b6a7`, or rewrite `down_revision` to real head.

**P1 still broken:**
- Frontend PM svelte-check: **133 errors** remain (was 138; only 5 shaved off). Distribution:
  - 91 in `routes/(app)/pm/[projectId]/[module]/+page.svelte` — includes 19 raw Svelte/TS syntax errors around lines 1890-1912; page will NOT compile.
  - 6 in `PMVersionComparePanel.svelte` — uses undeclared `diffLines` (ReferenceError at runtime); reads `oldV.entry_metadata` but frontend `types.ts:63/82/267` still calls the field `metadata` → backend rename never propagated to frontend types.
  - 9 in `PMTraceabilityGraph.svelte` + 8 in `PMMindMap.svelte` — `@xyflow/svelte` `nodes`/`edges` prop is `Writable<Node[]>` store, code passes plain arrays; `style`/`sourcePosition` types mismatched.
  - 5 in `PMImpactAnalysisView.svelte` + 4 in `agent.ts` — still call `response.success && response.data`, backend returns bare `{upstream, downstream}` / `AgentSuggestion[]`. Impact-analysis view permanently falls into else-branch.
  - `+page.svelte:156/217` reads `version.version_number` but frontend type defines it as `versionNumber` (camelCase drift).
- Smoke tests (`backend/tests/test_pm_smoke.py`): 10/10 ERROR at setup — `fixture 'client' not found`, `fixture 'auth_headers' not found`. No `conftest.py` in `backend/tests/`. Even if fixtures existed, assertions like `assert response.status_code in [200, 422, 500]` accept 500 as pass, so they provide zero real coverage.

**Root cause of re-verification failure:** sde-implementer treated the backend rename as complete without syncing `src/lib/apis/pm/types.ts` and the components that read `.metadata`. Also generated migration + tests without running `alembic heads` or `pytest --collect-only`.

**Why:** Coordinator declared "P0修复完成，请重新验收" on 2026-07-03T00:59Z. sde-tester re-ran the acceptance and found the above (task `b1c091fd` completed with report to coordinator inbox 125).

**How to apply:** When a batch of fixes touches backend field names, always search-and-replace across `src/lib/apis/pm/types.ts` and every `.svelte` that reads those fields. When creating an Alembic migration, first run `alembic heads` and chain `down_revision` to the true head. When creating pytest smoke tests, run `pytest --collect-only` before declaring done, and never accept `status_code in [..., 500]`.
