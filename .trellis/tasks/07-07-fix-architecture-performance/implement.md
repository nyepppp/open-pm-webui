# Implementation Plan: Fix Architecture Page Performance and Interaction Issues

## Phase 1: Tab Content Conditional Rendering (REQ-4)

**Goal**: Only render active tab content in DOM.

**Files**:
- `src/routes/(app)/pm/[projectId]/architecture/+page.svelte`

**Changes**:
1. Replace `class:hidden` with `{#if activeTab === 'xxx'}` blocks
2. Ensure each tab content is fully unmounted when not active
3. Keep tab bar and header always rendered

**Validation**:
- Switch tabs — only active tab content in DOM
- Check DevTools Elements panel

## Phase 2: D3 Mind-Map Fix (REQ-2, REQ-5)

**Goal**: Fix text rendering and reduce unnecessary re-renders.

**Files**:
- `src/lib/components/pm/mindmap/MindMapCanvas.svelte`

**Changes**:
1. Add debounce to ResizeObserver (300ms)
2. Memoize data changes (deep equality check before calling update())
3. Fix text fill color to ensure visibility
4. Verify text content is set correctly in D3 update cycle

**Validation**:
- Mind-map nodes display text
- Resize doesn't cause excessive re-renders

## Phase 3: Event Handler & Add Feature Fix (REQ-1, REQ-3)

**Goal**: Fix unresponsive buttons and navigation issues.

**Files**:
- `src/lib/components/pm/architecture/ModuleFeatureManager.svelte`
- `src/lib/components/pm/architecture/ModuleCard.svelte`

**Changes**:
1. Remove unnecessary `stopPropagation` in ModuleCard
2. Fix AddFeatureModal `moduleName` prop binding
3. Ensure `selectedModuleForFeature` is set before modal opens

**Validation**:
- Click "+ 添加功能" — modal opens with correct module name
- Navigation remains functional after clicking

## Phase 4: Add Module Fix (REQ-6)

**Goal**: Fix "+ 添加模块" button.

**Files**:
- `src/lib/components/pm/architecture/ModuleFeatureManager.svelte`

**Changes**:
1. Verify form visibility logic
2. Ensure `handleAddModule` doesn't cause infinite loop
3. Check that tab unmounting (Phase 1) doesn't break form state

**Validation**:
- Click "+ 添加模块" — form appears
- Submit form — module added, list refreshes

## Phase 5: Store Optimization (REQ-2, REQ-7)

**Goal**: Reduce derived store recalculation.

**Files**:
- `src/lib/stores/pm/architectureStore.ts`

**Changes**:
1. Add memoization to `aggregateModuleFeatureTree`
2. Use deep equality check or stringify comparison

**Validation**:
- Store updates don't cause full tree rebuild unless data changes
- Page remains responsive with large datasets

## Implementation Order

1. Phase 1 (Tab rendering) — unblock other fixes
2. Phase 4 (Add module) — depends on Phase 1
3. Phase 3 (Event handlers) — depends on Phase 1
4. Phase 2 (D3 fix) — independent
5. Phase 5 (Store optimization) — final optimization

## Rollback Points

- After each phase: `git diff` to review changes
- Full rollback: revert all 4 files to original state

## Validation Commands

```bash
# Build check
npm run build

# Type check
npm run check

# Lint
npm run lint
```

## Acceptance Criteria Checklist

- [ ] Navigation remains functional after interacting with any architecture page element.
- [ ] All clicks respond within 100ms.
- [ ] "+ 添加功能" button opens the modal and successfully adds a feature.
- [ ] Tab switching is instant with only active tab content in DOM.
- [ ] Mind-map nodes display module/feature names clearly.
- [ ] "+ 添加模块" button shows form and successfully adds a module.
- [ ] No console errors during normal interaction.
- [ ] Page remains responsive with 50+ modules/features.
