# Component Guidelines

> How components are built — extracted from `src/lib/components/pm/`.

---

## Svelte 5 Runes Pattern

All PM components use Svelte 5 runes syntax:

```svelte
<script lang="ts">
    interface Props {
        content?: string;
        onChange?: (content: string) => void;
        readonly?: boolean;
    }

    let { content = '', onChange, readonly = false }: Props = $props();

    let editor: Editor | null = $state(null);
    let loading = $state(false);
    let items = $derived(items.filter(i => i.active));
</script>
```

**Convention**:
- Use `$props()` with interface — NOT `export let`.
- Use `$state()` for reactive local state.
- Use `$derived()` for computed values.
- Use `$effect()` for side effects (with cleanup return).

---

## Component Structure

Every component follows this order:

```svelte
<script lang="ts">
    // 1. Imports
    import { onMount } from 'svelte';
    import type { ModuleEntry } from '$lib/apis/pm/types';

    // 2. Props interface + destructuring
    interface Props { ... }
    let { ... }: Props = $props();

    // 3. Local state ($state)
    let loading = $state(false);

    // 4. Derived state ($derived)
    let filteredItems = $derived(items.filter(...));

    // 5. Effects ($effect)
    $effect(() => { ... return () => cleanup(); });

    // 6. Functions
    async function loadData() { ... }

    // 7. Lifecycle (onMount)
    onMount(() => { ... });
</script>

<!-- Template -->
<div>...</div>

<!-- No <style> blocks — use Tailwind utility classes -->
```

---

## Props Conventions

1. **Always use `interface Props`** — Define props with a TypeScript interface.
2. **Destructure with defaults** — `let { readonly = false, onChange }: Props = $props();`
3. **Callback props use `on` prefix** — `onChange`, `onSelect`, `onDelete`, `onNavigate`.
4. **Optional props have defaults** — Never leave optional props without defaults.

---

## Styling Patterns

- **Tailwind CSS only** — No `<style>` blocks, no CSS modules, no styled-components.
- **Dark mode** — Always provide `dark:` variants: `bg-white dark:bg-gray-900`.
- **Common patterns**:

```html
<!-- Card -->
<div class="rounded-xl border border-gray-200 dark:border-gray-700 p-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">

<!-- Badge -->
<span class="text-xs px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">

<!-- Status indicator -->
<span class="inline-block w-2.5 h-2.5 rounded-full bg-yellow-400">
```

---

## Editor Components

PM has three editor types, each as a standalone component:

| Component | Use For | Key Props |
|-----------|---------|-----------|
| `PMRichEditor` | Rich text (PRD, meeting) | `content`, `onChange`, `readonly`, `showToc` |
| `PMFormEditor` | Structured forms (risk, FAQ) | `fields`, `data`, `onChange`, `onSubmit` |
| `PMMixedEditor` | Form + rich text (risk, competitor) | `fields`, `content`, `onChange` |

The module page (`[module]/+page.svelte`) selects the editor based on `moduleConfig[moduleType].editorType`.

---

## TipTap Editor Integration

### Convention: setContent second argument

TipTap v2+ `setContent` takes an options object, not a boolean:

```typescript
// Wrong (TipTap v1 API, causes TS error in v2+)
editor.commands.setContent(html, true);
editor.commands.setContent(html, false);

// Correct (TipTap v2+ API)
editor.commands.setContent(html, { emitUpdate: true });
editor.commands.setContent(html, { emitUpdate: false });
```

**Why**: The second argument changed from `boolean` to `SetContentOptions` in TipTap v2. Using the old API causes TypeScript errors and may behave unexpectedly at runtime.

### Pattern: Editor initialization with rAF guard

TipTap editors must be initialized after the DOM element is ready. Use `requestAnimationFrame` with a null guard:

```svelte
let editor: Editor | null = $state(null);
let element: HTMLDivElement | null = $state(null);
let editorReady = $state(false);

onMount(() => {
    if (!element) { isFallback = true; return; }
    requestAnimationFrame(() => {
        if (!element) { isFallback = true; return; }
        try {
            editor = new Editor({
                element,
                extensions: getPMExtensions(placeholder),
                content: content || '<p></p>',
                editable: !readonly,
                onCreate: () => { editorReady = true; },
                onDestroy: () => { console.log('editor destroyed'); }
            });
        } catch (err) {
            isFallback = true;
        }
    });
});
```

**Why**: Svelte may mount/unmount components rapidly. The rAF guard ensures the element still exists when the Editor constructor runs. The `editorReady` flag prevents toolbar interactions before initialization.

### Pattern: Content sync without $effect loops

Sync external `content` prop → editor using a non-reactive tracker to avoid infinite loops:

```svelte
let lastPropContent = content; // non-reactive tracker

$effect(() => {
    const newContent = content;
    if (newContent !== lastPropContent) {
        lastPropContent = newContent;
        if (editor && !editor.isDestroyed) {
            const currentHTML = editor.getHTML();
            if (newContent !== currentHTML) {
                editor.commands.setContent(newContent || '<p></p>', { emitUpdate: false });
            }
        }
    }
});
```

**Why**: Direct `$effect` on `content` that calls `setContent` triggers `onUpdate` → `onChange` → `content` change → loop. The `lastPropContent` tracker breaks the cycle by only calling `setContent` when the prop actually changed externally.

### Gotcha: PMDocumentImporter renders conditionally

`PMDocumentImporter` wraps its UI in `{#if editor}`. If the TipTap editor fails to initialize, the import button disappears entirely. This is correct behavior (import needs the editor to call `setContent`), but means **editor init bugs appear as missing import UI** rather than broken import UI.

---

## Svelte Template Nesting

### Don't: Mix if/else chains from different UI sections

```svelte
<!-- WRONG: prototype/schedule branches inside field.type chain -->
{#if field.type === 'textarea'}
    <textarea ... />
{:else if field.type === 'select'}
    <select ... />
{:else if field.type === 'combobox'}
    <input list=... />
{:else if moduleType === 'prototype'}  ← WRONG: different concern!
    <div>new entry prototype fields...</div>
{:else if moduleType === 'schedule'}   ← WRONG: different concern!
    <div>new entry schedule fields...</div>
{:else}
    <input type="text" ... />
{/if}
```

```svelte
<!-- CORRECT: field.type chain is self-contained, module-specific UI is separate -->
{#if field.type === 'textarea'}
    <textarea ... />
{:else if field.type === 'select'}
    <select ... />
{:else if field.type === 'combobox'}
    <input list=... />
{:else}
    <input type="text" ... />
{/if}
{/each}
<!-- Module-specific new-entry forms at the correct nesting level -->
{#if moduleType === 'prototype'} ... {/if}
{#if moduleType === 'schedule'} ... {/if}
```

**Why**: Svelte's `{#if}` / `{:else if}` / `{/if}` must form a single logical chain. Mixing conditions from different concerns (field rendering vs module-specific layout) causes template parsing errors and misrendered components.

### Common Mistake: Missing `{/if}` before edit drawer

When a page has both an entry editor panel and a separate edit drawer, ensure the entry editor's `{#if}` chain is fully closed with `{/if}` before the edit drawer's `{#if}` block begins. Otherwise Svelte treats the edit drawer branches as part of the entry editor chain.

---

## Common Mistakes

1. **Using `export let`** — Must use `$props()` in Svelte 5.
2. **Missing `dark:` variants** — All text and background classes need dark mode.
3. **Inline styles** — Use Tailwind classes, never `style="..."`.
4. **Not passing `onChange` callbacks** — Always propagate state changes upward.
5. **TipTap `setContent(html, bool)`** — Must use `setContent(html, { emitUpdate: bool })` in TipTap v2+.
6. **Missing `editorReady` guard** — Always show loading state until TipTap `onCreate` fires; otherwise toolbar buttons appear non-functional.
7. **Svelte template nesting across UI sections** — Never mix `{#if}` chains from different UI panels (entry editor vs edit drawer vs new-entry form).
8. **Reading `versionId` from only one source** — Always check BOTH `getEntryData(entry, 'versionId')` (data-level) AND `entry.versionId` (top-level). The version ID may be stored in either location depending on the save path.

---

## Version Association Pattern

Module entries can be associated with a project version. The version ID is stored in **two places** and must be read/written consistently.

### Convention: Dual-source version ID read

Always read `versionId` from both sources with fallback:

```svelte
{@const vid = getEntryData(entry, 'versionId') || entry.versionId}
```

**Why**: The `handleCreate` function writes to both `data.versionId` and top-level `versionId`, but older entries may only have one. The `saveEntryDoc` function also writes to both, but `saveEditDrawer` only spreads `data.versionId` through `data.data`. The dual-source read ensures all entries display correctly regardless of how they were saved.

### Convention: Dual-target version ID write

When saving, always write to **both** locations:

```typescript
await updateEntry(token, entryId, {
    data: { ...existingData, versionId: versionId },
    versionId: versionId  // top-level
});
```

**Why**: The card view reads `entry.versionId` first (via `getEntryData`), while the table `currentVersionNumber` column uses `entry.versionId` as a fallback when the UUID is resolvable. Writing to both ensures consistency across all views.

### Pattern: UUID resolution for `currentVersionNumber`

The `currentVersionNumber` field from the backend may contain a UUID instead of a human-readable version number. Always detect and resolve:

```svelte
{:else if col.key === 'currentVersionNumber'}
    {@const cvn = entry.currentVersionNumber}
    {@const entryVid = entry.versionId || getEntryData(entry, 'versionId')}
    {@const isUuid = cvn && /^[0-9a-f]{8}-/i.test(String(cvn))}
    {@const resolvedVid = isUuid ? cvn : entryVid}
    {@const matchedVersion = resolvedVid ? $versionList.find((v) => v.id === resolvedVid) : null}
    {@const displayVn = matchedVersion ? matchedVersion.versionNumber : (!isUuid && cvn ? cvn : '')}
```

**Why**: When the backend returns a UUID in `currentVersionNumber`, displaying it raw is meaningless to users. The resolution chain: (1) detect UUID format, (2) look up in `$versionList`, (3) fall back to raw value only if not a UUID.

### Gotcha: Auto-save must preserve versionId

The `saveEntryContentOnly` function (auto-save) runs without user interaction and must preserve the version association from the previous manual save:

```typescript
// Auto-save must include versionId from editing state
const autoVid = editingVersionId || editingEntry?.data?.versionId || '';
await updateEntry(token, editingEntryId, {
    data: { ...(editingEntry?.data || {}), versionId: autoVid },
    versionId: autoVid
});
```

**Why**: If auto-save omits `versionId`, the next auto-save cycle will overwrite the entry data without the version association, effectively un-associating the entry from its version silently.

---

## SPEC Module Pattern

### Convention: Module registration checklist

When adding a new PM module, update ALL of these locations:

1. `ModuleType` in `types.ts` — add the new module key
2. `moduleConfig` in `+page.svelte` — add config with `name`, `editorType`, and optional `tableColumns`/`formFields`
3. `moduleGroups` in `[projectId]/+page.svelte` — add to the appropriate category group (plan/design/execute/review/boundary)
4. `moduleLabels` in `[projectId]/+layout.svelte` — add display label
5. `svgIcons` in `[projectId]/+page.svelte` — add Heroicon path
6. `moduleCounts` in dashboard — add default count key

**Why**: Missing any of these causes either a TypeScript error, a missing navigation entry, or a broken breadcrumb. The checklist prevents partial registrations.

### Convention: SPEC metadata in `entry.data`

SPEC module stores structured metadata in the entry's `data` field:

```typescript
interface SpecMetadata {
    specCategory: 'functional' | 'prototype';
    role?: 'template';  // marks entry as a custom template
    relatedRequirements?: string[];  // entry IDs
    relatedParameters?: string[];    // entry IDs
}
```

**Why**: Using `data` (not `metadata`) is consistent with how other modules store structured fields (parameter, testcase, etc.). The `role: 'template'` marker allows custom templates to coexist with regular SPEC entries in the same `moduleType: 'spec'` bucket.

### Pattern: Template selection before creation

For modules with template support, use a dialog-first create flow:

```typescript
function handleSpecCreate() {
    showSpecTemplateDialog = true;
}

function handleSpecTemplateSelect(template: SpecTemplate | null) {
    if (template) {
        newContent = template.content;
        specCategory = template.category;
    }
    showSpecTemplateDialog = false;
    showNewForm = true;
}
```

**Why**: Setting `newContent` before `showNewForm = true` ensures the editor has content when it renders. The template dialog intercepts the create flow without modifying the existing `handleCreate` function.

### Pattern: Glossary panel with editor insert

Side panels that insert content into a TipTap editor use `editor.chain().focus().insertContent()`:

```typescript
function insertTerm(term: string, termEn: string, definition: string) {
    if (!editor) return;
    const html = `<p><strong>${term} (${termEn})</strong>: ${definition}</p>`;
    editor.chain().focus().insertContent(html).run();
}
```

**Why**: `focus()` ensures the editor cursor is active before insertion. The HTML format matches the TipTap content model. The null guard prevents errors when the editor instance is unavailable.

### Gotcha: `@const` tag placement in Svelte

`{@const}` declarations must be immediate children of `{#if}`, `{#each}`, or component blocks — NOT inside arbitrary `<div>` elements within those blocks:

```svelte
<!-- WRONG: @const inside a div child of {:else if} -->
{:else if moduleType === 'spec'}
    <div>
        {@const specCat = getEntryData(entry, 'specCategory')}  <!-- ERROR -->
        <span>{specCat}</span>
    </div>

<!-- CORRECT: Use inline expressions or move @const to block level -->
{:else if moduleType === 'spec'}
    <div>
        <span>{(getEntryData(entry, 'specCategory') || 'functional') === 'prototype' ? '前端原型' : '功能'}</span>
    </div>
```

**Why**: Svelte 5 restricts `{@const}` placement to specific structural blocks. Inside card list rendering within `{:else if}` branches, use inline expressions instead to avoid the `const_tag_invalid_placement` compiler error.

---

## Flowchart Module Pattern

### Convention: @xyflow/svelte@0.1.x store-based API

`@xyflow/svelte@0.1.x` uses Svelte `Writable` stores for `nodes` and `edges`, NOT `$state`:

```typescript
import { writable } from 'svelte/store';
import type { Node, Edge } from '@xyflow/svelte';

let nodesStore = writable<Node[]>([...]);
let edgesStore = writable<Edge[]>([...]);
```

Pass stores as props to `<SvelteFlow>`:

```svelte
<SvelteFlow nodes={nodesStore} edges={edgesStore} onconnect={handleConnect} />
```

**Why**: The 0.1.x API was designed around Svelte stores for two-way binding. The v1 API migrates to `$state` + `bind:nodes`, but 0.1.x requires `Writable`. Do NOT use `$state` for the nodes/edges arrays passed to SvelteFlow.

### Gotcha: @xyflow/svelte event syntax

`@xyflow/svelte@0.1.x` mixes callback props and Svelte 4 dispatched events:

- **Callback props** (lowercase): `onconnect`, `ondelete`, `onedgecreate`, `oninit`
- **Dispatched events** (Svelte 4 syntax): `on:nodeclick`, `on:paneclick`, `on:nodedragstop`

```svelte
<!-- CORRECT: callback props use no colon -->
<SvelteFlow onconnect={handleConnect} />

<!-- CORRECT: dispatched events use on: prefix -->
<SvelteFlow on:nodeclick={handleNodeClick} />

<!-- WRONG: mixing the two -->
<SvelteFlow onNodeClick={handleNodeClick} />
```

### Pattern: Custom node types with `as any`

When registering custom Svelte 5 component nodes with `@xyflow/svelte@0.1.x`, the TypeScript types expect Svelte 4 class-based components. Use `as any` to bridge the gap:

```typescript
import type { NodeTypes } from '@xyflow/svelte';
import DynamicNode from './flowchart/DynamicNode.svelte';

const nodeTypes: NodeTypes = {
    process: DynamicNode as any,  // Svelte 5 component vs Svelte 4 type mismatch
};
```

**Why**: @xyflow/svelte 0.1.x type definitions expect `ComponentType<SvelteComponent>` (Svelte 4 class), but Svelte 5 components are compiled differently. The `as any` cast is safe at runtime — the component renders correctly.

### Pattern: FlowchartData in entry.data.flowchart

Flowchart module stores its data in `entry.data.flowchart`:

```typescript
interface FlowchartData {
    nodes: FlowchartNode[];
    edges: FlowchartEdge[];
    viewport?: { x: number; y: number; zoom: number };
    nodeTypes?: Record<string, CustomNodeType>;
}
```

The editor receives `flowchartData` as a prop and calls `onChange(updatedFlowchartData)` on changes. The parent page persists it via:

```typescript
const d = { ...(editingEntry.data || {}) };
d.flowchart = updatedFlowchart;
editingEntry = { ...editingEntry, data: d };
saveStatus = 'unsaved';
triggerAutoSave();
```

**Why**: Consistent with how other modules store structured data in `entry.data` (parameter stores `data.fields`, spec stores `data.specCategory`, etc.).

### Pattern: Debounced auto-save from store subscriptions

Subscribe to SvelteFlow's writable stores and debounce the `onChange` callback:

```typescript
let saveTimer: ReturnType<typeof setTimeout> | undefined;

function emitChange(ns: Node[], es: Edge[]) {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
        onChange(/* transformed data */);
    }, 300);
}

nodesStore.subscribe((ns) => { currentNodes = ns; emitChange(ns, currentEdges); });
edgesStore.subscribe((es) => { currentEdges = es; emitChange(currentNodes, es); });
```

**Why**: Node position changes fire continuously during drag. Without debouncing, every pixel of drag triggers a save cycle. 300ms is a good balance between responsiveness and write amplification.

### Gotcha: SvelteFlow container requires explicit height

`<SvelteFlow>` will not render (blank canvas) if its container has no explicit height. `flex-1` alone is insufficient — the container needs a CSS `min-height` or fixed `height`:

```svelte
<!-- CORRECT: explicit min-height -->
<div class="w-full h-full relative" style="min-height: 400px;">
    <SvelteFlow ... />
</div>

<!-- WRONG: flex-1 alone may give 0px height -->
<div class="flex-1">
    <SvelteFlow ... />
</div>
```

**Why**: SvelteFlow uses the container's clientHeight to size its internal canvas. If the container has `height: 0` (common with `flex-1` without a constrained parent), the canvas is invisible.

### Gotcha: Store resync must guard against infinite loops

When `flowchartData` is a prop that updates via `onChange`, and stores are subscribed to emit changes, a circular loop can form:

```
onChange → prop change → $effect → store.set → subscribe → emitChange → onChange → ...
```

Guard the `$effect` with a deduplication check:

```typescript
let lastSyncedNodesJson = $state('');
$effect(() => {
    const xyNodes = toXyNodes(flowchartData.nodes);
    const json = JSON.stringify(xyNodes.map(n => n.id));
    if (json !== lastSyncedNodesJson) {
        lastSyncedNodesJson = json;
        nodesStore.set(xyNodes);
    }
});
```

**Why**: Without the guard, every `onChange` call triggers a prop update, which triggers the `$effect`, which sets stores, which fires subscriptions, which calls `emitChange`, which calls `onChange` again — infinite loop.

### Gotcha: `useOnSelectionChange` does NOT exist in @xyflow/svelte@0.1.39

This hook was added in later versions. For 0.1.x, use the Svelte 4 dispatched events instead:

```svelte
<!-- CORRECT: use dispatched events for selection tracking -->
<SvelteFlow
    on:nodeclick={(event) => { selectedNodeId = event.detail.node.id; }}
    on:paneclick={() => { selectedNodeId = null; }}
/>
```

**Why**: `useOnSelectionChange` is a v1 API. The 0.1.x API only provides `on:nodeclick` and `on:paneclick` dispatched events for tracking node selection.

### Pattern: Parameter↔Flowchart reverse index (derived)

To show which flowchart nodes reference a parameter, use a `$derived.by()` reverse index instead of persisting `flowchartRefs` on parameter entries:

```typescript
let flowchartEntries = $state<any[]>([]);

interface FlowchartRef {
    flowchartId: string; flowchartTitle: string;
    nodeId: string; nodeLabel: string; type: 'input' | 'output';
}

let paramFlowchartRefs = $derived.by(() => {
    const map = new Map<string, FlowchartRef[]>();
    for (const fc of flowchartEntries) {
        const nodes = (fc.data?.flowchart?.nodes || []) as any[];
        for (const node of nodes) {
            for (const pid of (node.data?.inputParams || [])) {
                const refs = map.get(pid) || [];
                refs.push({ flowchartId: fc.id, flowchartTitle: fc.title,
                    nodeId: node.id, nodeLabel: node.data?.label || '', type: 'input' });
                map.set(pid, refs);
            }
            for (const pid of (node.data?.outputParams || [])) {
                const refs = map.get(pid) || [];
                refs.push({ flowchartId: fc.id, flowchartTitle: fc.title,
                    nodeId: node.id, nodeLabel: node.data?.label || '', type: 'output' });
                map.set(pid, refs);
            }
        }
    }
    return map;
});
```

**Why**: Derived index is always up-to-date with flowchart data. No extra API writes needed. No stale `flowchartRefs` field to sync. Load `flowchartEntries` when parameter module is active via `getEntries(token, projectId, 'flowchart')`.

### Pattern: Parameter delete → flowchart cleanup

When a parameter entry is deleted, clean up all flowchart nodes that reference it:

```typescript
async function cleanupFlowchartRefsForParam(paramId: string) {
    const refs = paramFlowchartRefs.get(paramId) || [];
    const affectedFcIds = [...new Set(refs.map(r => r.flowchartId))];
    for (const fcId of affectedFcIds) {
        const fcEntry = flowchartEntries.find(e => e.id === fcId);
        const fcData = { ...(fcEntry.data || {}) };
        const flowchart = fcData.flowchart || { nodes: [], edges: [] };
        flowchart.nodes = (flowchart.nodes || []).map((node: any) => {
            const inputParams = (node.data?.inputParams || []).filter((id: string) => id !== paramId);
            const outputParams = (node.data?.outputParams || []).filter((id: string) => id !== paramId);
            if (inputParams.length === (node.data?.inputParams || []).length &&
                outputParams.length === (node.data?.outputParams || []).length) return node;
            return { ...node, data: { ...node.data, inputParams, outputParams } };
        });
        fcData.flowchart = flowchart;
        await updateEntry(token, fcId, { data: fcData });
    }
}
```

Call this before `deleteEntry` in `handleDelete` when `moduleType === 'parameter'`.
