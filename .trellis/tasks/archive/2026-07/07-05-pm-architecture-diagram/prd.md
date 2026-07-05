# Product Architecture Diagram - Auto-sync with module/feature versions

## Goal

Make the product architecture diagram auto-sync with modules and features as they change, providing a real-time overview of the product's full feature architecture across versions.

## Background

- `product-architecture` module type already exists in `ModuleType`
- `PMMindMap` component renders `MindMapNode[]` using `@xyflow/svelte`
- `MindMapNode` type: `{ id, projectId, parentId, label, type, position, metadata, moduleRef, createdAt, updatedAt }`
- `ProductArchitecture` type stores `nodes: MindMapNode[]` and `autoExtracted: boolean`
- The module page already has `isMindmapView` rendering path
- `moduleRef` field on `MindMapNode` already supports referencing a module entry

## Requirements

### R1: Auto-Extract Architecture from Module Entries
- Add a backend endpoint `POST /pm/projects/{id}/architecture/auto-extract` that:
  - Scans all module entries in the project
  - Groups entries by `moduleType` as top-level branches
  - Creates child nodes for each entry (using entry title as label)
  - Sets `moduleRef` to the entry ID for navigation
  - Stores result as a product-architecture entry with `autoExtracted: true`
- Auto-extracted nodes include `metadata.versionId` to track which version they belong to

### R2: Version-Aware Architecture View
- Architecture diagram nodes show version badges (from their linked entry's versionId)
- Filter architecture by project version (dropdown selector)
- When filtering by version, only show entries associated with that version
- "All versions" view shows every entry with version badges

### R3: Change Detection & Sync
- Add a "Sync" button on the architecture page that re-runs auto-extract
- Compare new extraction with existing architecture entry
- Show diff: new entries (green), removed entries (red), modified entries (yellow)
- User confirms sync to update the architecture

### R4: Navigation from Architecture
- Clicking a node with `moduleRef` navigates to the referenced entry's module page
- Node tooltip shows: entry title, module type, version, status, priority

## Acceptance Criteria

- [ ] Backend `auto-extract` endpoint creates architecture from project module entries
- [ ] Architecture nodes have `moduleRef` and `metadata.versionId`
- [ ] Version filter dropdown on architecture page
- [ ] Filtering by version shows only matching entries
- [ ] "Sync" button re-extracts and shows diff before applying
- [ ] Clicking architecture nodes navigates to referenced entries
- [ ] Node tooltips show entry metadata
- [ ] Follows existing `PMMindMap` component patterns (writable stores, debounced save)

## Out of Scope

- Auto-sync on every entry change (too expensive — manual sync button is sufficient)
- Drag-and-drop reordering of architecture nodes
- Custom node styling per module type
