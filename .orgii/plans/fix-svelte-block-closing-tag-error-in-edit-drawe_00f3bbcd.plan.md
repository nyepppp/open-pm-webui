# Fix Svelte Block Closing Tag Error in Edit Drawer

## Context

File: `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`

The "Table Edit Drawer" (lines 1318–1472) uses an `{#if}` block to conditionally wrap content in an extra `<div>` for roadmap/schedule module types. Svelte does not allow `{#if}` blocks to span across HTML element boundaries — opening a `<div>` inside an `{#if}` and closing it in a separate `{#if}` is invalid.

Current broken structure (simplified):
```
{#if showEditDrawer && editDrawerEntry}
  <div class="fixed inset-0 z-40 bg-black/30" ...></div>
  <div class="fixed z-50 h-full {moduleType === 'roadmap' || moduleType === 'schedule' ? 'inset-0 ...' : 'top-0 right-0 ...'} ...">
    {#if moduleType === 'roadmap' || moduleType === 'schedule'}   ← line 1322
      <div class="w-full max-w-lg rounded-2xl ...">              ← line 1323
    {/if}                                                         ← line 1324 — ERROR
      ... drawer content (header, form fields, footer) ...
    {#if moduleType === 'roadmap' || moduleType === 'schedule'}   ← line 1468
      </div>                                                      ← line 1469
    {/if}                                                         ← line 1470
  </div>
{/if}
```

## Approach

1. **Remove the cross-boundary `{#if}` blocks** (lines 1322–1324 and 1468–1470) that try to conditionally open/close a wrapping `<div>`.

2. **Duplicate the drawer content** into two branches of a single `{#if ... } {:else}` block at the outer container level:
   - **Roadmap/Schedule branch**: renders the centered modal wrapper `<div class="fixed inset-0 z-50 flex items-center justify-center">` containing the rounded card `<div class="w-full max-w-lg rounded-2xl ...">` with all drawer content inside.
   - **Other modules branch**: renders the side drawer `<div class="fixed top-0 right-0 w-full max-w-md ...">` with the same drawer content inside.

3. **Extract the shared drawer content** (header bar, form fields section, footer buttons) into a local Svelte snippet or simply duplicate the ~150 lines. Given the file size and complexity, the cleanest approach is to extract the inner content into a snippet using Svelte 5's `{#snippet}` syntax, then call it from both branches.

   However, since this file may not yet use Svelte 5 snippet syntax and the content is relatively self-contained, the simplest correct fix is to **restructure the conditional at the container level** — move the `{#if}` to wrap the entire outer `<div class="fixed z-50 ...">` element, giving each branch its own complete container with the inner content duplicated.

   **Preferred minimal fix**: Instead of duplicating ~150 lines, restructure the outer container to use conditional classes and always render the inner card div, but adjust the layout so the card div is always present (just with different styling):

   ```
   <div class="fixed z-50 h-full {moduleType === 'roadmap' || moduleType === 'schedule' ? 'inset-0 flex items-center justify-center' : 'top-0 right-0 w-full max-w-md shadow-xl flex flex-col'} bg-white dark:bg-gray-900 transition-transform">
     <div class="{moduleType === 'roadmap' || moduleType === 'schedule' ? 'w-full max-w-lg rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 flex flex-col max-h-[80vh]' : 'flex flex-col h-full'}">
       ... all drawer content ...
     </div>
   </div>
   ```

   This eliminates both `{#if}` blocks entirely by using conditional CSS classes on the inner `<div>`. For roadmap/schedule it gets the rounded card styling; for other modules it becomes a plain flex column that fills the side drawer.

## Key Files

- `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
  - **Lines 1322–1324**: Remove the `{#if moduleType === 'roadmap' || moduleType === 'schedule'}` opening block and its `{/if}` close. Change the `<div>` on line 1323 to always be present with conditional classes.
  - **Lines 1321**: Adjust the outer container's class to remove the redundant conditional classes for the non-roadmap case (the `shadow-xl flex flex-col` is already on the inner div).
  - **Lines 1468–1470**: Remove the closing `{#if}` block and `</div>`.
  - The inner `<div>` (currently line 1323) gets a ternary class: roadmap/schedule → card styles; else → `flex flex-col h-full` to fill the side drawer.

## Risks & Open Questions

- The visual appearance for non-roadmap modules (side drawer) may shift slightly if the inner `<div>` class changes from nothing to `flex flex-col h-full`. Need to verify the side drawer still looks correct after the change.
- The outer container on line 1321 has duplicate conditional classes (`shadow-xl flex flex-col` appears in both branches of the ternary). These can be cleaned up since the inner div will handle the flex layout.
