# Prototype Annotation - Link prototype elements to requirements/SPEC/params

## Goal

Enable users to annotate prototype screens by marking regions/components and linking them to related requirements, SPEC documents, and parameter entries. This creates traceability between visual prototypes and their backing specifications.

## Background

- `PMAnnotationPanel` already exists — it renders `EntryAnnotation[]` with click/remove/AI-modify callbacks
- `EntryAnnotation` type exists: `{ id, entryId, entryVersionId, textRange, selectedText, content, highlightColor, createdBy, createdAt, updatedAt }`
- The `prototype` module type already exists in `ModuleType` union
- The `spec` module already has `specCategory: 'prototype'` classification
- `PMRelationPicker` component exists for linking entries

## Requirements

### R1: Prototype Entry Annotation Enhancement
- Extend `EntryAnnotation` to support `elementRef` field — a structured reference to a specific UI element on the prototype (e.g., component name, bounding box, screenshot region)
- Allow annotations to be created by selecting text ranges in the prototype's rich text content (existing behavior) AND by selecting named elements/components

### R2: Annotation → Requirement/SPEC/Parameter Linking
- When creating or editing an annotation, allow the user to link it to one or more entries from other modules (requirement, spec, parameter)
- Store linked entry IDs in `annotation.linkedEntries: string[]`
- Display linked entries as clickable badges in the annotation card
- Clicking a linked entry navigates to that entry's module page

### R3: Annotation Boundary Markers
- Allow annotations to include boundary descriptions: which functional boundary/area of the prototype this annotation covers
- Store as `annotation.boundary: string` (free text, with autocomplete from existing boundaries)
- Filter annotations by boundary in the annotation panel

### R4: Default Values & Parameter Indicators
- Annotations linked to parameter entries should display the parameter's default value and data type
- Show parameter indicators (type badge, required badge, default value) inline in the annotation card

## Acceptance Criteria

- [ ] `EntryAnnotation` type extended with `elementRef`, `linkedEntries`, `boundary` fields
- [ ] Annotation creation/editing dialog supports linking to entries from other modules
- [ ] `PMAnnotationPanel` shows linked entries as clickable badges
- [ ] Clicking a linked entry navigates to the correct module page
- [ ] Boundary field with autocomplete and filter support
- [ ] Parameter indicators (type, required, default) shown for parameter-linked annotations
- [ ] Backend API updated to persist new annotation fields
- [ ] All changes follow existing component/store/API patterns

## Out of Scope

- Visual region selection on screenshot/image prototypes (future enhancement)
- AI-powered auto-linking of annotations to requirements
