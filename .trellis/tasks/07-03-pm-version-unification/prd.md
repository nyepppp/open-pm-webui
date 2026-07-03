# PM模块版本信息统一

## Goal

Fix 3 interrelated version bugs in the PM module so that version information is consistently created, linked, and displayed across all modules.

## Background

GitHub Issue: nyepppp/open-pm-webui#1 (CLOSED, unfixed)

The PM module has a dual version system:
- **Project versions** (`pm_version`): project-level milestones/releases managed via the version selector
- **Entry versions** (`pm_entry_version`): per-entry snapshots tracking content changes over time

These two levels are connected by `pm_entry_version.project_version_id` and `pm_relation.version_id`.

Three bugs break this system:

### Bug 1: New entries don't auto-create initial entry version

**Evidence**: `routers/pm.py:151-180` — `create_entry` auto-creates a `PMEntity` for traceability but does NOT create an initial `PMEntryVersion`. The first version is only created when the user explicitly calls `create_entry_version` (line 250).

**Impact**: New entries show no version history until manually saved. The version history dropdown is empty for newly created entries.

### Bug 2: Traceability content versions aren't linked to project versions

**Evidence**:
- `PMEntryVersion.project_version_id` column exists (models/pm.py:76) but is only populated when `create_project_version_snapshot` (routers/pm.py:1204) is called, which hardcodes `projectVersionId` into metadata.
- `get_project_version_entries` (routers/pm.py:1169-1183) looks up entries by matching `entry.data.versionId == version_id` — a fragile JSON field lookup instead of using the dedicated `project_version_id` column.
- `PMRelation.version_id` (models/pm.py:139) exists but relations created by the auto-entity logic don't set it.

**Impact**: The traceability graph and project version snapshot don't correctly reflect which entry versions belong to which project version.

### Bug 3: Version info columns not unified across modules

**Evidence**: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte:34-101` — each module defines its own `tableColumns` in `moduleConfig`. Some modules have a version column (`roadmap` has `versionId`), most don't. No module consistently shows `currentVersionNumber` or `branchName` which are fields on `ModuleEntry` (types.ts:67-68).

**Impact**: Users can't see version information at a glance in the table view for most modules.

## Requirements

### REQ-1: Auto-create entry version on entry creation
- When `create_entry` succeeds, automatically create an initial `PMEntryVersion` (v1) snapshot of the entry.
- The auto-created version must be non-blocking (same pattern as auto-entity creation: try/except + warning log).
- Frontend must refresh version history after entry creation so the dropdown shows v1 immediately.

### REQ-2: Link entry versions to project versions
- When a project version snapshot is created (`create_project_version_snapshot`), set `project_version_id` on each `PMEntryVersion` instead of embedding it in metadata.
- Fix `get_project_version_entries` to query by `PMEntryVersion.project_version_id` instead of the fragile `entry.data.versionId` JSON lookup.
- Relation version linking (`PMRelation.version_id`) is deferred — auto-entity creation runs at entry creation time when no project version context exists on the backend.

### REQ-3: Unify version info column across all table-based modules
- Add a `currentVersionNumber` column to all table-based module configurations that don't already have a version column.
- Display format: version number + branch indicator (e.g., "v2 (feature-branch)" or "v1").
- The column should appear before the "status" column.

## Acceptance Criteria

- [ ] **AC-1.1**: Creating a new entry via `POST /projects/{id}/entries` automatically creates an initial v1 entry version record in `pm_entry_version`.
- [ ] **AC-1.2**: The v1 entry version captures the entry's initial `content`, `data` (as metadata), and `module_type`.
- [ ] **AC-1.3**: Frontend version history dropdown shows v1 immediately after entry creation without manual refresh.
- [ ] **AC-2.1**: `create_project_version_snapshot` sets `project_version_id` on each `PMEntryVersion` row instead of embedding in metadata JSON.
- [ ] **AC-2.2**: `get_project_version_entries` queries `PMEntryVersion.project_version_id` instead of `entry.data.versionId`.
- [ ] **AC-3.1**: All table-based modules (requirement, parameter, testcase, roadmap, prototype, schedule) display a version info column.
- [ ] **AC-3.2**: Version column shows `currentVersionNumber` with branch indicator when applicable.
- [ ] **AC-3.3**: Version column appears before the "status" column in the table layout.

## Technical Notes

- Auto-version creation must follow the same non-blocking pattern as auto-entity creation (try/except + warning log at `routers/pm.py:174-178`).
- `PMEntryVersionForm` already supports `project_version_id` (routers/pm.py:277). The schema column exists.
- Frontend `ModuleEntry` type already has `currentVersionNumber` and `branchName` fields (types.ts:67-68).
- The `moduleConfig` table column definitions are in `+page.svelte:34-101`. Adding a version column requires updating `tableColumns` arrays and the table rendering logic.

## Out of Scope

- Migrating historical entry versions that lack `project_version_id` (separate data migration task).
- Changing the version number format or branching UI.
- Adding version info to rich-text editor modules (prd, meeting) which don't have table views.
- Linking `PMRelation.version_id` during auto-entity creation (deferred — no backend project version context at entry creation time).
