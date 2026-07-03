# Fix PM Page: Create Project Failure + Sidebar Layout

## Context

Two issues reported on `/pm` page:

1. **创建项目失败** — Clicking "创建" button fails silently or with generic error. Root cause: PM API calls go to `http://localhost:8080/api/v1/pm/projects` but the backend may not be running or the `pm_project` / `pm_entry` / `pm_version` tables don't exist in the database. The PM model classes inherit from `Base` but there's no migration or auto-creation step for these tables.

2. **侧边栏展开后右边工具台界面不会动态调整** — When the PM sidebar navigation expands, the right-side content area doesn't adjust its width. All other pages in OpenWebUI (admin, workspace, notes, home) use `transition-width duration-200` + `md:max-w-[calc(100%-var(--sidebar-width))]` pattern tied to `$showSidebar`, but the PM layout (`+layout.svelte`) just uses `h-full w-full` without this responsive pattern.

## Approach

### Fix 1: Create Project — Backend table auto-creation + Frontend error handling

1. **Add PM table auto-creation in lifespan** — In `backend/open_webui/main.py` lifespan function, after other startup tasks, add `Base.metadata.create_all` call that includes the PM tables. Since PM models import `Base` from `open_webui.internal.db`, they're already registered in the metadata. We just need to ensure the import of `open_webui.models.pm` happens before `create_all` is called (it already is via the router import at line 502).

2. **Add `create_all` for PM tables** — Add a startup step in the lifespan that calls `Base.metadata.create_all` to ensure PM tables exist. This follows the same pattern used by pgvector/opengauss for their tables.

3. **Improve frontend error handling** — In `src/routes/(app)/pm/+page.svelte`, the `handleCreate` function catches errors but only shows `e.message || '创建失败'`. Improve to show more specific messages (network error, 404, 500, etc.) and add a loading state on the create button.

### Fix 2: Sidebar layout — Add responsive width to PM layout

1. **Update `src/routes/(app)/pm/+layout.svelte`** — Add `showSidebar` store import and apply the standard responsive width pattern:
   - Wrap the outer div with `transition-width duration-200 ease-in-out` 
   - Add `md:max-w-[calc(100%-var(--sidebar-width))]` when sidebar is shown
   - This matches the pattern used by admin, workspace, notes, and home layouts

2. **Update `src/routes/(app)/pm/[projectId]/+layout.svelte`** — Same responsive width pattern for the project workspace layout.

## Key Files

- `backend/open_webui/main.py` — Add PM table auto-creation in lifespan (~line 665, after redis init)
- `src/routes/(app)/pm/+layout.svelte` — Add `showSidebar` responsive width pattern
- `src/routes/(app)/pm/[projectId]/+layout.svelte` — Add `showSidebar` responsive width pattern  
- `src/routes/(app)/pm/+page.svelte` — Improve create project error handling with loading state

## Risks & Open Questions

- **Database compatibility**: `Base.metadata.create_all` only creates tables that don't exist. It won't alter existing tables if the schema changes. For production, proper Alembic migrations would be needed. But for dev/initial setup, `create_all` is sufficient and matches how other parts of OpenWebUI handle this.
- **Backend not running**: If the backend isn't running at all, no frontend fix will help. The improved error handling will at least show a clear "无法连接服务器" message instead of a generic failure.
- **`get_async_db_context` pattern**: The PM model methods use `get_async_db_context(db)` which creates a new session if `db` is None, or reuses the passed session. This is the same pattern as `folders.py` and should work correctly once tables exist.
