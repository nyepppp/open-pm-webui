# Expose and Implement PM Toolbench

## Context

The current Open WebUI frontend shown in the browser still exposes the default navigation: chat, search, notes, workspace, and workspace tabs such as models/tools. A PM route already exists at `src/routes/(app)/pm/+page.svelte`, but there is no visible PM entry in the main sidebar, so users cannot discover or access PM-specific functionality from the WebUI.

The backend has PM API routing already reachable under `/api/v1/pm/...`; previous verification showed `/api/v1/pm/templates` is an authenticated Open WebUI endpoint. The immediate problem is therefore not only API availability, but productization in the frontend: visible PM navigation, a PM landing workspace, and basic interactions that make PM functions usable.

This implementation should adapt the PM workflow direction onto the existing Open WebUI/SvelteKit base rather than replacing Open WebUI.

## Approach

1. Add a visible PM entry to the main app navigation.
   - Locate the existing sidebar/nav component that renders `新对话`, `搜索`, `笔记`, `工作空间`.
   - Add a first-class item such as `产品工作台` / `PM 工作台` linking to `/pm`.
   - Preserve the existing Open WebUI layout, auth behavior, and responsive sidebar behavior.

2. Turn `/pm` into a usable PM toolbench landing page.
   - Use the existing `src/routes/(app)/pm/+page.svelte` route as the primary page instead of creating a disconnected UI elsewhere.
   - Provide a dashboard-style layout with clear modules:
     - 项目 / 工作区概览
     - 需求文档 / PRD
     - 需求拆分 / 任务规划
     - 模板 / Prompt / 工具
     - 溯源与评审记录
   - Make the page visually distinct from default Open WebUI model/tool pages so the user can immediately see PM-specific functionality.

3. Connect the PM page to existing backend PM APIs where available.
   - Add or reuse frontend API helpers under `src/lib/apis/` for `/api/v1/pm/templates` and any discovered PM endpoints.
   - Load templates or workspace data on mount using `localStorage.token` like existing Open WebUI API helpers.
   - If no backend data exists yet, show actionable empty states rather than a blank page.

4. Implement the first usable PM workflow actions.
   - Add quick actions for creating/selecting a PRD/workspace or starting from a template, depending on available backend endpoints.
   - For missing backend endpoints, keep frontend buttons disabled or routed to planned placeholders with explicit labels, rather than silently failing.
   - Ensure PM workflow copy follows the user’s requirement for traceability: clearly label source/依据 fields and avoid implying generated content is verified without source.

5. Build and verify the frontend.
   - Run `npm run check` to validate Svelte/TypeScript.
   - Run `npm run build` if feasible so backend can serve the built frontend at 8080.
   - Verify in browser or via HTTP that `/pm` is reachable and that the sidebar exposes the PM entry.
   - Verify existing Open WebUI routes such as `/workspace/tools` still render.

## Key Files

- `src/routes/(app)/pm/+page.svelte`
  - Expand or replace the current PM route content with the PM toolbench dashboard and first usable PM workflow UI.

- `src/lib/components/...` sidebar/navigation component
  - Add the visible `PM 工作台` / `产品工作台` navigation item linking to `/pm`.
  - Exact file to be confirmed during implementation from the sidebar component that renders the currently visible `新对话`, `搜索`, `笔记`, `工作空间` entries.

- `src/lib/apis/pm.ts` or existing PM API helper file if present
  - Add frontend fetch helpers for authenticated PM endpoints such as `/api/v1/pm/templates`.

- `backend/open_webui/routers/...` PM router files if needed
  - Only adjust backend if the frontend reveals missing or broken PM API behavior required for the first working page.

- `src/lib/i18n/...` locale files if the touched navigation labels require i18n integration
  - Add Chinese/English labels only if the existing sidebar uses translation keys rather than inline labels.

## Risks & Open Questions

- The existing PM page may already contain partial implementation; implementation should preserve useful existing PM code after reading it, not blindly replace it.
- Some PM backend endpoints may be authenticated and may require the logged-in user token; verification should be done while logged in or with expected `401` behavior documented.
- If the backend has only templates and no full project/PRD CRUD yet, this iteration should make the PM entry and landing page visible and usable with templates/empty states, then leave deeper PRD editing as the next implementation slice.
- The screenshot shows a browser password-save popover covering the page; this is unrelated to PM functionality and should not drive code changes unless it blocks UI testing.