# Data Model: SPEC Module Bug Fixes

**Date**: 2026-07-10
**Feature**: SPEC Module Bug Fixes

## Overview

No new entities or schema changes are required for this feature. The fixes use existing data structures. This document describes the existing entities involved and how they are used.

## Existing Entities

### ModuleEntry

Represents any entry in a PM module (requirement, parameter, spec, etc.).

```typescript
interface ModuleEntry {
  id: string;
  projectId: string;
  moduleType: ModuleType;
  title: string;
  status: string;
  priority?: string;
  content?: string;
  data?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  createdAt: number;
  updatedAt: number;
  version?: number;
  currentVersionNumber?: string;
}
```

**Used in**: `PMRelationPicker` to display real requirement/parameter entries for association.

### EntryAnnotation

Represents a comment/annotation on a rich-text entry.

```typescript
interface EntryAnnotation {
  id: string;
  entryId: string;
  entryVersionId: string;
  textRange: { from: number; to: number };
  selectedText: string;
  content: string;
  highlightColor: string;
  createdBy: string;
  createdAt: number;
  updatedAt: number;
  boundary?: string;
  elementRef?: { componentName?: string; selector?: string };
  linkedEntries?: string[];
}
```

**Stored in**: `entry.data.annotations` (array of EntryAnnotation)

**Used in**: `PMAnnotationPanel` to display and manage annotations.

### Spec Data (entry.data for spec module)

```typescript
interface SpecData {
  specCategory: 'functional' | 'prototype';
  relatedRequirements: string[];  // Array of requirement entry IDs
  relatedParameters: string[];    // Array of parameter entry IDs
  annotations?: EntryAnnotation[];  // Annotations on this SPEC
  versionId?: string;
}
```

**Stored in**: `entry.data` for entries with `moduleType === 'spec'`

## Relationships

```
ModuleEntry (spec)
  ├── relatedRequirements → ModuleEntry[] (requirement)
  ├── relatedParameters → ModuleEntry[] (parameter)
  └── annotations → EntryAnnotation[]
```

## Validation Rules

- `relatedRequirements` must contain valid requirement entry IDs (enforced by UI selection)
- `relatedParameters` must contain valid parameter entry IDs (enforced by UI selection)
- `annotations` is an array; each annotation must have a unique `id`

## State Transitions

No state machine changes. The fixes are:

1. **Read transition**: `PMRelationPicker` reads real `ModuleEntry[]` from API instead of mock data
2. **Write transition**: `onAnnotationsChange` persists to server via `updateEntry()` instead of local-only
3. **UI transition**: `PMSpecGlossaryPanel` receives editor instance and can insert content
