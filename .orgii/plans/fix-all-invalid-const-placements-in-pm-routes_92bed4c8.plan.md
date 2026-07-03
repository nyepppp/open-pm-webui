# Fix all invalid `{@const}` placements in PM routes

## Context
The `{@const}` Svelte 5 tag must be the immediate child of a block directive (`{#if}`, `{#each}`, `{#key}`, `{:else if}`, `{:else}`, `{#snippet}`) or special elements (`<svelte:fragment>`, `<svelte:boundary>`, `<Component>`). Placing it inside a regular HTML element like `<div>` or `<button>` causes a compile error, which SvelteKit surfaces as a 500 Internal Error.

The original bug was in `[projectId]/+page.svelte:277` (already fixed). After auditing all PM route files, **2 more invalid placements** were found in `[module]/+page.svelte`.

## Audit Results

### Valid `{@const}` placements (no fix needed)
- `[module]/+page.svelte:926-933` — inside `{#key}` block ✅
- `[module]/+page.svelte:956-965` — inside `{#each}` block ✅
- `[module]/+page.svelte:973` — inside `{#each}` block ✅
- `[module]/+page.svelte:1010,1017,1030,1035,1038,1041,1044,1047,1058` — inside `{:else if}` blocks ✅
- `[module]/+page.svelte:1070` — inside `{:else}` block ✅
- `workflow/+page.svelte:248-251` — inside `{#each}` block ✅
- `traceability/+page.svelte:173-174` — inside `{#each}` block ✅

### Invalid `{@const}` placements (need fix)

**Fix 1: `[module]/+page.svelte:1137`** — `{@const nodeCount}` inside `<div>`

```svelte
// BEFORE (invalid):
{@const nodeCount = (getEntryData(entry, 'nodes') || []).length}
<div class="text-xs text-gray-400 mt-1">🗺️ {nodeCount || 0} 个节点</div>

// AFTER (inline the expression):
<div class="text-xs text-gray-400 mt-1">🗺️ {(getEntryData(entry, 'nodes') || []).length || 0} 个节点</div>
```

**Fix 2: `[module]/+page.svelte:1653`** — `{@const entryVid}` inside `<div>`

```svelte
// BEFORE (invalid):
<div>
    <div class="text-xs font-medium text-gray-500 uppercase mb-2">版本信息</div>
    {@const entryVid = traceEntry.versionId || getEntryData(traceEntry, 'versionId') || ''}
    {#if entryVid}
        <span ...>{$versionList.find((v: any) => v.id === entryVid)?.versionNumber || entryVid}</span>
    {:else}<span class="text-xs text-gray-400">未绑定版本</span>{/if}
</div>

// AFTER (move {#if} to be the parent, {const} inside {#if}):
<div>
    <div class="text-xs font-medium text-gray-500 uppercase mb-2">版本信息</div>
    {#if traceEntry.versionId || getEntryData(traceEntry, 'versionId')}
        {@const entryVid = traceEntry.versionId || getEntryData(traceEntry, 'versionId')}
        <span ...>{$versionList.find((v: any) => v.id === entryVid)?.versionNumber || entryVid}</span>
    {:else}<span class="text-xs text-gray-400">未绑定版本</span>{/if}
</div>
```

For Fix 2, the `{@const}` is moved inside the `{#if}` block (which is a valid parent). The condition checks truthiness first, then the `{@const}` safely extracts the value inside the block. The `|| ''` fallback is removed since we only enter the block when the value is truthy.

## Approach
1. Apply Fix 1: inline `nodeCount` expression at line 1137
2. Apply Fix 2: restructure `{@const entryVid}` + `{#if}` at line 1653 to put `{#if}` first
3. Verify with `svelte-check` that no compile errors remain in PM route files

## Key Files
- `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` — lines 1137 and 1653

## Risks & Open Questions
- Fix 2 uses `{@const}` inside `{#if}` which is valid, but the expression `traceEntry.versionId || getEntryData(traceEntry, 'versionId')` is evaluated twice (once in condition, once in `{@const}`). This is acceptable for a simple property access.
- No other PM route files have invalid `{@const}` placements.
