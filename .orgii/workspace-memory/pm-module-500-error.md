---
name: PM Module 500 Error Fix
description: PM module 500 error from Svelte 4 event syntax and missing API exports; ALL FIXES APPLIED AND BUILD VERIFIED
type: workspace
---

The PM module pages crashed with 500 Internal Error. Root causes and fixes applied:

1. **Svelte 4 `on:eventName` on SvelteFlow** — PMMindMap.svelte lines 283-285: `on:nodeClick`→`onnodeclick`, `on:paneClick`→`onpaneClick`, `on:viewportChange`→`onviewportchange`. Also fixed in chat/Overview/Flow.svelte (lines 40-46) and Overview/View.svelte (line 181).

2. **Svelte 4 `|stopPropagation` modifier** — PMDocumentImporter.svelte:92 and PMTableOfContents.svelte:105: replaced with `onclick={(e) => e.stopPropagation()}`.

3. **Missing API helper exports** — `src/lib/apis/pm/index.ts` was missing `getOne<T>`, `create<T>`, `update<T>`, `remove<T>` generic helpers that 14+ files in `apis/pm/` imported. Added them. Also restored `relation.ts` to use these helpers.

**Why:** Svelte 5 compile failures from invalid event syntax + broken imports. Build verified passing (`vite build` succeeded).

**How to apply:** All fixes are applied. If adding new PM API submodules, use the `getOne`/`create`/`update`/`remove` helpers from `./index` (or `../index` from `modules/` subdirectory). For Svelte component events on third-party libs, always use callback props (`onnodeclick=`, `onpaneClick=`) not `on:eventName`.
