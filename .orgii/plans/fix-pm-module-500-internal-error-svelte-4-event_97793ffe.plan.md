# Fix PM Module 500 Internal Error

## Context
The PM module pages are crashing with a 500 Internal Error. The root cause is **Svelte 4 event syntax** in PMMindMap.svelte that is invalid in Svelte 5. The `@xyflow/svelte` v0.1.x library (Svelte 5 compatible) uses callback props (`onNodeClick`, `onPaneClick`, etc.) instead of the Svelte 4 `on:eventName` directive syntax.

Other files in the same codebase already use the correct Svelte 5 style (e.g., `traceability/+page.svelte` uses `onnodeclick=...`), confirming the migration path.

## Approach

1. **Fix PMMindMap.svelte** — Replace three Svelte 4 `on:` event directives on the `<SvelteFlow>` component with Svelte 5 callback prop syntax:
   - `on:nodeClick={handleNodeClick}` → `onnodeclick={handleNodeClick}`
   - `on:paneClick={handlePaneClick}` → `onpaneClick={handlePaneClick}`
   - `on:viewportChange={handleViewportChange}` → `onviewportchange={handleViewportChange}`

   Note: Svelte 5 component event props are lowercase (following DOM convention). The traceability page already uses `onnodeclick` successfully.

2. **Also fix Overview/Flow.svelte and Overview/View.svelte** — These chat components also use `on:nodeclick` and `on:click` Svelte 4 syntax on SvelteFlow and ControlButton, which will cause 500 errors when those components render:
   - `Flow.svelte:40` — `on:nodeclick=...` → `onnodeclick=...`
   - `Flow.svelte:41` — `oninit=...` → `oninit=...`
   - `Flow.svelte:46` — `on:click=...` → `onclick=...`
   - `View.svelte:181` — `on:nodeclick=...` → `onnodeclick=...`

## Key Files
- `src/lib/components/pm/PMMindMap.svelte` — Lines 283-285: Replace `on:nodeClick`, `on:paneClick`, `on:viewportChange` with `onnodeclick`, `onpaneClick`, `onviewportchange`
- `src/lib/components/chat/Overview/Flow.svelte` — Lines 40-46: Replace `on:nodeclick`, `oninit`, `on:click` with Svelte 5 syntax
- `src/lib/components/chat/Overview/View.svelte` — Line 181: Replace `on:nodeclick` with `onnodeclick`

## Risks & Open Questions
- The exact casing for SvelteFlow callback props needs verification. The traceability page uses `onnodeclick` (all lowercase), but SvelteFlow may also accept `onNodeClick` (camelCase). We should match whatever works in the existing traceability page.
- There may be additional Svelte 4 syntax issues in other PM files not yet discovered. After fixing these, the dev server should be checked for remaining compile errors.
