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
