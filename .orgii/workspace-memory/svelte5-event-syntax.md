---
name: Svelte 5 Migration Event Syntax
description: Svelte 4→5 migration: event modifiers and on: directives are invalid; use callback props and e.stopPropagation() instead
type: feedback
---

In Svelte 5, two major event syntax changes break at compile time:
1. **Event modifiers** (`onclick|stopPropagation`, `on:click|preventDefault`, etc.) are removed. Replace with inline calls: `onclick={(e) => e.stopPropagation()}`, `on:click` → `onclick={(e) => { e.preventDefault(); ... }}`.
2. **Component event directives** (`on:eventName={handler}`) are removed for Svelte 5-compatible libraries. Use callback props instead: `on:nodeClick={fn}` → `onnodeclick={fn}`, `on:paneClick={fn}` → `onpaneclick={fn}`.

Additionally, missing module exports cause build failures even when Svelte syntax is correct. The PM API layer (`src/lib/apis/pm/index.ts`) must export `getOne`, `create`, `update`, `remove` generic helpers since 14+ submodule files (version.ts, relation.ts, modules/*.ts) import them. If these are missing, `vite build` fails with `"getOne" is not exported by "src/lib/apis/pm/index.ts"`.

**Why:** The workspace is on Svelte 5 and `@xyflow/svelte` v0.1.x (Svelte 5 compatible). The old syntax causes compile failures (500 errors). The traceability page already demonstrates the correct pattern (`onnodeclick`, `onpaneclick` lowercase). The missing exports issue was discovered during build verification after fixing Svelte syntax — the Svelte errors masked the import errors.

**How to apply:** When editing .svelte files, never use `on:eventName` or `|modifier` syntax. Always use Svelte 5 `on<event>={handler}` callback props. For DOM events with modifiers, call the DOM method inline. Check existing working files (e.g., traceability page) for the correct casing of third-party component callback props. When adding PM API submodules, ensure `index.ts` exports the generic helpers they need.
