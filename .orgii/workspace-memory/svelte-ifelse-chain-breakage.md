---
name: Svelte if-else chain structure in +page.svelte is broken
 description: The module editor +page.svelte has a broken if-else chain around lines 1890-1912, causing Svelte compilation failure.

**Why:** The Svelte `{#if}` block starting at line 1871 (`{#if moduleType === 'product-architecture'}`) is closed at line 1876 (`{/if}`), but the subsequent `{:else}` at line 1890 is not properly nested within an outer `{#if}` block. This creates an orphaned else branch that Svelte cannot compile.

**How to apply:** When editing +page.svelte, always verify that every `{:else}` and `{:else if}` has a matching opening `{#if}` tag. Use an editor with Svelte syntax highlighting or run `npx svelte-check` after any if-else chain modification. The file at src/routes/(app)/pm/[projectId]/[module]/+page.svelte is particularly prone to this due to its 2266-line length and deeply nested conditional rendering logic.
type: feedback
---

**Rule:** When editing large Svelte files with nested `{#if}`/`{:else if}`/`{:else}` blocks, always verify that every `{:else if}` and `{:else}` has a matching `{#if}` opening tag. Use editor bracket-matching or run `npx svelte-check` after every structural edit.

**Why:** On 2026-07-03, `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` had a broken if-else chain. The structure was:
- Line 1563: `{#if moduleType === 'prd'}` ... 
- Line 1869: `{:else if isMindmapView}` ...
- Line 1890: `{:else}` ...
- Line 1912: `{:else if moduleType === 'prototype'}` ← **ORPHANED** — no matching `{#if}`

This caused Svelte compiler to emit "Declaration or statement expected" errors at lines 1890-1912, making the entire module editor page unrenderable. The `{:else if moduleType === 'prototype'}` block was likely intended to be inside a nested `{#if editingEntry}` block but was placed at the wrong nesting level during a previous edit.

**How to apply:**
- Before committing changes to large Svelte templates, run `npx svelte-check --tsconfig ./tsconfig.json` to catch structural errors.
- When adding new module-specific editor blocks, wrap them in a single `{#if editingEntry}` block with nested `{:else if moduleType === '...'}` conditions, rather than appending them to an existing if-else chain at the wrong level.
- Consider extracting large per-module editor blocks into separate sub-components to reduce nesting depth and prevent this class of error.