# Design: Fix Architecture Page Performance and Interaction Issues

## Architecture Overview

The architecture page (`/pm/:id/architecture`) consists of three tabs sharing the same data store. The root causes of performance issues are:

1. **All tab content rendered simultaneously** — hidden tabs still consume DOM/render resources
2. **D3 mind-map re-renders on every reactive change** — expensive data joins run unnecessarily
3. **Derived store recalculation** — `aggregatedTree` rebuilds on every store update
4. **Event handler conflicts** — `stopPropagation` in cards may block navigation

## Proposed Changes

### 1. Tab Content Rendering (REQ-4)

**Current**: All three tabs use `class:hidden` — content is in DOM but hidden via CSS.

```svelte
<!-- Current -->
<div class:hidden={activeTab !== 'mindmap'}>
  <MindMapCanvas ... />
</div>
<div class:hidden={activeTab !== 'modules'}>
  <ModuleFeatureManager ... />
</div>
```

**Proposed**: Use `{#key}` or `{#if}` to mount/unmount tab content, preserving only active tab in DOM.

```svelte
<!-- Proposed -->
{#if activeTab === 'mindmap'}
  <div class="h-[calc(100vh-200px)]">
    <MindMapCanvas ... />
  </div>
{:else if activeTab === 'modules'}
  <div class="h-[calc(100vh-200px)]">
    <ModuleFeatureManager ... />
  </div>
{:else if activeTab === 'params'}
  <div class="h-[calc(100vh-200px)]">
    <ParameterTable ... />
  </div>
{/if}
```

**Trade-off**: Tab switching will unmount/mount components instead of CSS toggle. This is acceptable because:
- Mind-map D3 SVG is expensive to keep in DOM
- ModuleFeatureManager card grid is also expensive
- ParameterTable has its own state that can be re-hydrated

### 2. D3 Mind-Map Optimization (REQ-2, REQ-5)

**Current**: `MindMapCanvas` has a reactive `$effect` that calls `update()` on every data/size change, running full D3 data joins.

**Issues**:
- `update()` runs on every `$effect` tick (lines 370-377)
- Text content may not render due to D3 data join timing
- ResizeObserver triggers re-renders on every pixel change

**Proposed fixes**:
1. **Debounce ResizeObserver**: Only update D3 after resize stops (300ms debounce)
2. **Memoize data**: Only re-render when `data` prop actually changes (deep equality)
3. **Fix text rendering**: Ensure text is set correctly in D3 update cycle
4. **Add `willReadFrequently` canvas hint** if switching to canvas (out of scope — keep SVG)

**Text fix** (lines 263-264 in MindMapCanvas.svelte):
```javascript
// Current - may not work due to D3 data join timing
nodeMerge.select('text')
  .text(d => truncateText(d.data.name, nodeWidth - 20));

// Fix: Use .join() pattern or ensure text is set on enter + update
nodeMerge.select('text')
  .text(d => truncateText(d.data.name, nodeWidth - 20));
```

The actual fix may be that the text is being set but the color matches the background. Need to verify text fill color.

### 3. Derived Store Memoization (REQ-2)

**Current**: `aggregatedTree` is a derived store that recalculates on every `parameterEntries` or `archEntries` change.

**Proposed**: Add memoization to `aggregateModuleFeatureTree` using a simple cache key.

```typescript
// In architectureStore.ts
let lastParamEntries: ModuleEntry[] = [];
let lastArchEntries: ModuleEntry[] = [];
let cachedTree: TreeModule[] = [];

function aggregateModuleFeatureTree(
  paramEntries: ModuleEntry[],
  architectureEntries: ModuleEntry[]
): TreeModule[] {
  // Simple memoization
  if (paramEntries === lastParamEntries && architectureEntries === lastArchEntries) {
    return cachedTree;
  }
  // ... existing logic ...
  lastParamEntries = paramEntries;
  lastArchEntries = architectureEntries;
  cachedTree = result;
  return result;
}
```

Actually, since Svelte stores use reference equality, this won't work as-is. Better approach: use a custom derived store with deep equality check or use `derived` with a custom equality function.

### 4. Event Handler Fixes (REQ-1, REQ-3, REQ-6)

**ModuleCard click handler** (lines 37-40):
```svelte
<!-- Current - may capture events -->
<div onclick={() => onSelect?.()} role="button" tabindex="0">
```

**Fix**: Ensure click handlers don't call `stopPropagation` unless necessary. The `onclick` on the card wrapper should not interfere with navigation.

**AddFeatureModal** (lines 278-281 in ModuleFeatureManager):
```svelte
<!-- Current -->
onAddFeature={() => {
  selectedModuleForFeature = mod.name;
  showAddFeatureForm = true;
}}
```

The issue is that `selectedModuleForFeature` is set but the modal's `moduleName` prop may not be reactive. Need to ensure `moduleName` updates when `selectedModuleForFeature` changes.

### 5. Add Module Form (REQ-6)

**Current**: Form shows/hides based on `showAddModuleForm` state.

**Issue**: After clicking "添加模块", the form may not appear or may cause other components to become unresponsive.

**Likely cause**: The form is rendered inside a flex container with `overflow-y-auto`. If the form causes layout shift, it may trigger ResizeObserver in MindMapCanvas (if still mounted), causing a re-render loop.

**Fix**: Ensure tab content is properly unmounted when not active (see #1 above).

## Data Flow

```
architectureStore (parameterEntries, archEntries)
  ↓
derived: aggregatedTree
  ↓
+page.svelte (activeTab, selectedModule, selectedFeature)
  ↓
  ├─ MindMapCanvas (data={treeToMindMap($aggregatedTree)})
  ├─ ModuleFeatureManager (modules={$aggregatedTree})
  │   ├─ ModuleCard[]
  │   └─ AddFeatureModal
  └─ ParameterTable (entries={$parameterEntries})
```

## Compatibility

- Svelte 5 runes (`$state`, `$derived`, `$effect`)
- D3 v7+
- Tailwind CSS v3+

## Rollback

All changes are localized to:
- `src/routes/(app)/pm/[projectId]/architecture/+page.svelte`
- `src/lib/components/pm/mindmap/MindMapCanvas.svelte`
- `src/lib/components/pm/architecture/ModuleFeatureManager.svelte`
- `src/lib/stores/pm/architectureStore.ts`

No backend changes. Rollback by reverting these files.
