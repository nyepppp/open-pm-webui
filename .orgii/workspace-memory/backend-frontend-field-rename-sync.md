---
name: Backend field renames must propagate to frontend types and readers
description: A backend Pydantic/SQLAlchemy field rename is only half done until src/lib/apis/pm/types.ts and every .svelte/.ts reader is updated in the same batch.

**Why:** When `metadata` was renamed to `entry_metadata`/`entity_metadata` in backend/models/pm.py (P0 fix), the frontend types.ts still had `metadata?: Record<string, any>` and PMVersionComparePanel.svelte still referenced `.metadata`. This caused runtime undefined values and TypeScript errors. Similarly, `version_number` vs `versionNumber` naming inconsistency exists between backend (snake_case) and frontend (camelCase) types.

**How to apply:** Any backend field rename must include:
1. Update backend model + Pydantic schema
2. Update src/lib/apis/pm/types.ts frontend types
3. Update all .svelte components that read the field
4. Verify with `npx svelte-check` and runtime testing
5. Never mark "done" until both backend and frontend compile clean
type: feedback
---

**Rule:** When you rename a backend response field (Pydantic model attribute or SQLAlchemy column that is returned via `from_attributes=True`), in the same commit also update `src/lib/apis/pm/types.ts` and every `.svelte`/`.ts` file that reads that field. Do not mark the task complete until `svelte-check` reports 0 new errors on affected components.

**Why:** On 2026-07-03, the SQLAlchemy `metadata` → `entry_metadata` / `entity_metadata` rename fixed the backend startup blocker, but `src/lib/apis/pm/types.ts:63/82/267` still declared the field as `metadata?`, and `PMVersionComparePanel.svelte:71-72` was updated to read `oldV.entry_metadata`. Result: type-check reports `Property 'entry_metadata' does not exist on type 'EntryVersion'`; at runtime other components reading `.metadata` get `undefined` because the backend now emits `entry_metadata`. The version-diff metadata panel became silently non-functional.

**How to apply:**
- Before renaming: `grep -r "\.<old_name>" src/lib/apis/pm src/lib/components/pm src/routes/\(app\)/pm` to find every reader.
- In the same commit, update: (1) SQLAlchemy Column, (2) Pydantic Model + Form, (3) Table Class assignment sites, (4) `src/lib/apis/pm/types.ts` interfaces, (5) every component reader, (6) any REST payload constructors.
- Verify with `npx svelte-check --tsconfig ./tsconfig.json` — the PM error count must not increase.
- The same rule applies to camelCase/snake_case drift: e.g. backend emitting `version_number` while frontend types define `versionNumber` — one side or the other must be adjusted; do not declare done until both agree.
