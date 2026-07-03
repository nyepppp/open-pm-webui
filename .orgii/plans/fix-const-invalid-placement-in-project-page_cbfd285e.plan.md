# Fix `{@const}` invalid placement causing 500 error on project page

## Context
Navigating to `/pm/[projectId]` results in a **500 Internal Error**. The root cause is a Svelte 5 compile error at `src/routes/(app)/pm/[projectId]/+page.svelte:277` — a `{@const}` tag is placed directly inside a `<button>` element, which is not a valid parent. Svelte 5 requires `{@const}` to be the immediate child of a block directive (`{#if}`, `{#each}`, `{#snippet}`, etc.) or specific elements (`<svelte:fragment>`, `<svelte:boundary>`, `<Component>`). The compile failure prevents the entire page from rendering, hence the 500.

## Approach
1. **Remove the `{@const}` tag** and inline the expression into the `{#if}` condition and the `getVersionLabel()` call.
2. The expression `item.versionId || (item.data || item.metadata || {}).versionId || ''` is used to extract a version ID. In the `{#if}` check, the `|| ''` fallback is unnecessary (we only enter the block when the value is truthy). In the `getVersionLabel()` argument, we use the same expression without the fallback since we're already inside the truthy branch.

**Change** (lines 276–280):

```svelte
// BEFORE (invalid — causes compile error → 500):
<!-- Version badge -->
{@const itemVid = item.versionId || (item.data || item.metadata || {}).versionId || ''}
{#if itemVid}
    <span class="px-1.5 py-0.5 rounded text-[10px] bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400 flex-shrink-0">{getVersionLabel(itemVid)}</span>
{/if}

// AFTER (valid):
{#if item.versionId || (item.data || item.metadata || {}).versionId}
    <span class="px-1.5 py-0.5 rounded text-[10px] bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400 flex-shrink-0">{getVersionLabel(item.versionId || (item.data || item.metadata || {}).versionId)}</span>
{/if}
```

The expression is duplicated (condition + argument) but this is minimal and avoids introducing extra abstraction. The comment `<!-- Version badge -->` is also removed as dead weight.

## Key Files
- `src/routes/(app)/pm/[projectId]/+page.svelte` — lines 276–280: remove `{@const}`, inline the version ID expression into the `{#if}` condition and `getVersionLabel()` call.

## Risks & Open Questions
- The duplicated expression is slightly less DRY, but it's a simple two-occurrence pattern with no maintenance risk.
- No backend changes needed — the 500 is purely a Svelte compile error, not an API issue.
