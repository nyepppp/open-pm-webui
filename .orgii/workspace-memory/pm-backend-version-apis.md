---
name: PM Backend Entry-Level Version APIs
 description: Backend database tables and API endpoints for entry-level versioning (snapshots, branches, merges)
 type: workspace
 ---
 
 New database tables added to `backend/open_webui/models/pm.py`:
 - `PMEntryVersion` — stores entry version snapshots (content, metadata, branch, change summary)
 - `PMEntryBranch` — stores branches per entry (name, source version, status)
 - `PMEntryMerge` — stores merge records with conflicts
 
 New API endpoints added to `backend/open_webui/routers/pm.py`:
 - `GET /projects/{pid}/entries/{eid}/versions` — list entry versions
 - `POST /projects/{pid}/entries/{eid}/versions` — create version snapshot (auto-captures current entry content)
 - `GET /projects/{pid}/entries/{eid}/versions/{vid}` — get specific version
 - `POST /projects/{pid}/entries/{eid}/versions/{vid}/switch` — restore entry to version
 - `GET /projects/{pid}/entries/{eid}/branches` — list branches
 - `POST /projects/{pid}/entries/{eid}/branches` — create branch
 - `GET /projects/{pid}/entries/{eid}/merges` — list merges
 - `POST /projects/{pid}/entries/{eid}/merges` — create merge
 
 **Why:** The frontend (`src/lib/apis/pm/version.ts`) already had the correct API calls, but the backend router (`pm.py`) only had project-level version APIs. Entry-level version history, branching, and merging were completely unimplemented, causing all version features to fail silently.
 
 **How to apply:** When testing version features, verify that the backend tables are created via Alembic migration. The frontend `PMVersionHistoryDropdown`, `PMVersionComparePanel`, `PMVersionBranchDialog`, and `PMVersionMergePanel` components should now work with real data. Ensure `saveAsNewVersion()` in `+page.svelte` calls `createEntryVersion()` which hits the new backend endpoint.