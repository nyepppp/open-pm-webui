# Fix architecture page performance and interaction issues

## Goal

Fix severe performance and interaction issues on the `/pm/:id/architecture` page that cause UI lag, unresponsive clicks, broken navigation, and missing mind-map content.

## Background

The architecture page displays product architecture in three tabs: Mind Map (D3.js tree), Module/Feature Management (card grid), and Parameter Table. Users report that clicking elements causes the entire page to freeze or become unresponsive, navigation breaks, tab switching is laggy, and mind-map nodes show no content.

## Requirements

### REQ-1: Fix "click breaks navigation" issue
- **Problem**: Clicking page components causes the navigation bar to stop working.
- **Evidence**: Annotation #1 — "点击页面组件后导航栏也用不了了"
- **Likely cause**: Event handlers (especially in ModuleCard or MindMapCanvas) may be calling `event.stopPropagation()` or capturing events globally, preventing navigation events from bubbling. Alternatively, a full-page re-render or D3 SVG overlay may be intercepting clicks.
- **Acceptance**: After clicking any component on the architecture page, the top/side navigation remains functional.

### REQ-2: Fix click lag / unresponsiveness
- **Problem**: Clicking elements (cards, buttons) has severe lag.
- **Evidence**: Annotation #2 — "点击依旧很卡"; Annotation #7 — "点击都没有响应"
- **Likely cause**: 
  - `ModuleFeatureManager` re-renders entire card grid on every state change.
  - `aggregatedTree` derived store recalculates on every store update.
  - D3 `update()` function in `MindMapCanvas` runs expensive data joins and transitions on every reactive tick.
- **Acceptance**: Clicking any element responds within 100ms; no perceptible lag.

### REQ-3: Fix "Add Feature" button unresponsive
- **Problem**: "+ 添加功能" button in ModuleCard does nothing when clicked.
- **Evidence**: Annotation #3 — "点击无响应"
- **Likely cause**: In `ModuleFeatureManager.svelte`, the `onAddFeature` callback sets `selectedModuleForFeature` and `showAddFeatureForm`, but `AddFeatureModal` receives `moduleName={selectedModuleForFeature}` which may be empty or the modal may not be receiving the correct props. Also, the modal's `bind:show` may not be reactive.
- **File**: `src/lib/components/pm/architecture/ModuleFeatureManager.svelte` lines 278-281, `AddFeatureModal.svelte`
- **Acceptance**: Clicking "+ 添加功能" opens the Add Feature modal with the correct module name pre-filled.

### REQ-4: Fix tab switching lag
- **Problem**: Switching between "思维导图", "模块/功能", "参数表格" tabs is laggy.
- **Evidence**: Annotation #4 — "切换也很卡"
- **Likely cause**: All three tab contents are rendered in the DOM simultaneously with `class:hidden`. The MindMapCanvas D3 SVG and ModuleFeatureManager card grid are both mounted even when not visible, consuming resources. Switching tabs triggers re-renders of all hidden content.
- **File**: `src/routes/(app)/pm/[projectId]/architecture/+page.svelte` lines 150-276
- **Acceptance**: Tab switching is instant (<50ms); only the active tab's content is in the DOM.

### REQ-5: Fix mind-map nodes showing no content
- **Problem**: Mind-map nodes (rect elements) display no text/content.
- **Evidence**: Annotation #5 — "节点看不到内容"
- **Likely cause**: In `MindMapCanvas.svelte`, the D3 `update()` function appends `<text>` elements but may not set the text content correctly, or the `truncateText` function returns empty. Alternatively, text color matches background in dark/light mode.
- **File**: `src/lib/components/pm/mindmap/MindMapCanvas.svelte` lines 228-234, 263-264
- **Acceptance**: Mind-map nodes clearly display module/feature names.

### REQ-6: Fix "Add Module" button no effect
- **Problem**: "+ 添加模块" button in ModuleFeatureManager has no effect.
- **Evidence**: Annotation #6 — "点击无效果"; Annotation #8 — "点击添加模块后其他组件无效了"
- **Likely cause**: The `showAddModuleForm` state toggles but the form may not render due to conditional logic error, or the form renders but `handleAddModule` fails silently. Also, after clicking, other components become invalid — suggesting a state corruption or infinite re-render loop.
- **File**: `src/lib/components/pm/architecture/ModuleFeatureManager.svelte` lines 94-99, 216-240
- **Acceptance**: Clicking "+ 添加模块" shows the add-module form; submitting adds the module and refreshes the list.

### REQ-7: Fix overall interaction responsiveness
- **Problem**: The module structure interaction is sluggish and needs refactoring.
- **Evidence**: Annotation #7 — "这个交互重构一下吧。太卡了。点击都没有响应"
- **Likely cause**: Combination of all above issues — excessive re-renders, non-virtualized lists, D3 re-rendering on every state change, and derived store recalculation.
- **Acceptance**: The entire module/feature management section feels snappy; scrolling, expanding, and clicking are all responsive.

## Acceptance Criteria

- [ ] Navigation remains functional after interacting with any architecture page element.
- [ ] All clicks respond within 100ms.
- [ ] "+ 添加功能" button opens the modal and successfully adds a feature.
- [ ] Tab switching is instant with only active tab content in DOM.
- [ ] Mind-map nodes display module/feature names clearly.
- [ ] "+ 添加模块" button shows form and successfully adds a module.
- [ ] No console errors during normal interaction.
- [ ] Page remains responsive with 50+ modules/features.

## Out of Scope

- Rewriting the D3 mind-map visualization (fix rendering bugs only, not redesign).
- Backend API changes.
- Adding new features beyond bug fixes.

## Technical Notes

### Key Files
- `src/routes/(app)/pm/[projectId]/architecture/+page.svelte` — Main page with tab switching logic
- `src/lib/components/pm/architecture/ModuleFeatureManager.svelte` — Module/feature card grid
- `src/lib/components/pm/architecture/ModuleCard.svelte` — Individual module card
- `src/lib/components/pm/mindmap/MindMapCanvas.svelte` — D3 mind-map visualization
- `src/lib/components/pm/ModuleFeatureTree.svelte` — Sidebar tree navigation
- `src/lib/stores/pm/architectureStore.ts` — Store with `aggregatedTree` derived store
- `src/lib/utils/excalidrawDataConverter.ts` — `treeToMindMap()` converter

### Known Issues
1. **Tab content always rendered**: All three tabs use `class:hidden` instead of conditional rendering, causing hidden tabs to consume resources.
2. **D3 re-renders on every reactive tick**: `MindMapCanvas` `$effect` triggers `update()` on any data/size change, running expensive D3 data joins.
3. **Derived store recalculation**: `aggregatedTree` derived from `parameterEntries` and `archEntries` recalculates on every store update.
4. **Event propagation**: ModuleCard click handlers may interfere with global navigation.
5. **AddFeatureModal props**: `moduleName` prop may not be correctly passed or reactive.

## Open Questions

- None — all issues are clearly defined from user annotations and code inspection.
