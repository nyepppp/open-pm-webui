# Data Model: 产品架构页面缺陷修复与交互重构

**Date**: 2026-07-10
**Feature**: specs/005-arch-bugfix-redesign

## Entity Changes

### No schema changes required

This feature is a bugfix and interaction redesign. The data model (Module, Function, Parameter, VersionRecord, DemandRelation) is already defined in spec 004 and implemented. No new fields or tables are needed.

### Key Data Flow Fix

**Current (broken)**:
```
+page.svelte → architectureStore (new) → ArchModule[] → ArchitectureTable (ignores props, uses old store)
ArchitectureTable → architectureStore (old) → architecture API → /api/pm/modules
```

**Target (fixed)**:
```
+page.svelte → architectureStore (old) → architecture API → /api/pm/modules
ArchitectureTable → architectureStore (old) → architecture API → /api/pm/modules
```

Both components use the same store and API layer. No data transformation needed.

### Batch Parameter Create Data Flow

**New flow**:
```
BatchParameterForm → validate all rows → submit all rows sequentially → 
  if any fails: rollback created entries → show error
  if all succeed: architectureStore.createParameter() × N → refresh table
```

### MindMapView Data Flow

**Current**: Hardcoded root node `{ name: '产品架构' }`
**Target**: `projectName` prop from `+page.svelte` → `getProject(projectId)` → project.name

## Component Inventory

### Keep (modify)
| Component | Changes |
|-----------|---------|
| `+page.svelte` | Remove version selector/AI button; use old architectureStore; pass projectName to MindMapView |
| `ArchitectureTable.svelte` | Remove props-based data flow; use old store directly; fix createVersion field mapping; fix demand relation click handler |
| `MindMapView.svelte` | Add projectName prop; use as root node label; show version+description in NodeDetailModal |
| `NodeDetailModal.svelte` | Ensure version and description are shown |
| `ModuleForm.svelte` | Fix create_version field mapping; ensure demand relation modal works |

### New (create)
| Component | Purpose |
|-----------|---------|
| `BatchParameterForm.svelte` | Batch parameter creation form with N rows, add/remove row, all-or-nothing submit |

### Delete
| Component | Reason |
|-----------|--------|
| `ModuleTable.svelte` | Replaced by ArchitectureTable per FR-010 |
| `ModuleCard.svelte` | Only referenced by ModuleTable/ModuleFeatureManager |
| `ModuleFeatureManager.svelte` | Only referenced by ModuleTable |
| `ModuleFeatureTree.svelte` | Only referenced by ModuleFeatureManager |
| `src/lib/stores/pm/architectureStore.ts` (relevant parts) | Replaced by old architectureStore; remove architectureHierarchy, convertToArchModules, aggregatedTree |

### Keep unchanged
| Component | Reason |
|-----------|--------|
| `VersionHistoryPopover.svelte` | Works correctly |
| `DemandRelationModal.svelte` | Works correctly |
| `DemandRelationTag.svelte` | Works correctly |
| `ArchitectureError.svelte` | Works correctly |
| `ArchitectureLoading.svelte` | Works correctly |
| `ArchitectureTabBar.svelte` | May keep for future use |
| `EditItemModal.svelte` | Used by ArchitectureTable |
| `PMVersionSelector.svelte` | Keep for future use, just remove from +page |
