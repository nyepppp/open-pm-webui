# Implementation Plan: SPEC Module Bug Fixes

**Branch**: `[001-spec-module-bugfix]` | **Date**: 2026-07-10 | **Spec**: [specs/001-spec-module-bugfix/spec.md](specs/001-spec-module-bugfix/spec.md)

**Input**: Feature specification from `/specs/001-spec-module-bugfix/spec.md`

## Summary

Fix three critical bugs in the SPEC module: (1) replace mock data with real project entity associations for requirements, modules, features, and parameters; (2) fix the non-functional "术语参考" (terminology reference) insert action in the glossary panel; (3) fix annotation data sync and the non-functional AI Modify button in the annotation panel.

## Technical Context

**Language/Version**: TypeScript 5.x, Svelte 5 (runes), Tailwind CSS

**Primary Dependencies**: SvelteKit, TipTap (rich editor), Open WebUI API layer

**Storage**: SQLite (local) / PostgreSQL (production) via Open WebUI ORM

**Testing**: Manual browser testing, no automated test suite

**Target Platform**: Web (Chrome/Firefox/Safari)

**Project Type**: Web application (Open WebUI extension)

**Performance Goals**: Selector load <500ms, insert action <1s, annotation sync <2s

**Constraints**: Must maintain backward compatibility with existing SPEC data; AI features require manual fallback when AI service unavailable

**Scale/Scope**: Single project, up to 1000+ entries per module

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Manual-First Productivity | ✅ Pass | All fixes support manual operation; no AI dependency for core functionality |
| II. Module-Centric Architecture | ✅ Pass | Fixes stay within SPEC module scope, no cross-module schema changes |
| III. AI-Assisted, Human-Confirmed | ✅ Pass | AI Modify button fix maintains human-confirmation flow per Constitution |
| IV. Data Isolation & Traceability | ✅ Pass | All associations scoped by project_id; no cross-project data access |
| V. Version-Controlled Documentation | ✅ Pass | No document version changes required for these bug fixes |
| VI. Agent Platform Capabilities | ✅ Pass | No agent tool/skill changes required |

## Project Structure

### Documentation (this feature)

```text
specs/001-spec-module-bugfix/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── lib/
│   ├── components/
│   │   └── pm/
│   │       ├── PMRelationPicker.svelte     # Fix: replace mock data with real API calls
│   │       ├── PMSpecGlossaryPanel.svelte  # Fix: wire insertTerm to editor
│   │       ├── PMAnnotationPanel.svelte    # Fix: annotation sync + AI modify
│   │       └── PMRichEditor.svelte         # Fix: handleAiModify + annotation sync
│   └── apis/
│       └── pm/
│           └── index.ts                    # Already has getEntries API
├── routes/
│   └── (app)/
│       └── pm/
│           └── [projectId]/
│               └── [module]/
│                   └── +page.svelte        # SPEC editor wiring for relations/glossary/annotations
```

**Structure Decision**: Single frontend project (SvelteKit). The fixes are localized to the PM module components and the SPEC editor page. No backend changes needed — the existing `getEntries` API already supports fetching real data.

## Complexity Tracking

> No Constitution violations requiring justification.

---

## Phase 0: Research

See [research.md](research.md) for detailed findings.

### Key Findings

1. **PMRelationPicker** (`src/lib/components/pm/PMRelationPicker.svelte:66-92`): `loadItems()` has a `TODO: Replace with actual API call` and returns hardcoded mock data. The component is used in the SPEC editor to select related requirements, modules, features, and parameters.

2. **PMSpecGlossaryPanel** (`src/lib/components/pm/PMSpecGlossaryPanel.svelte:23-27`): `insertTerm()` checks `if (!editor) return;` but the `editor` prop is never passed from the parent (`+page.svelte`), so the insert button silently does nothing.

3. **PMAnnotationPanel + PMRichEditor**: 
   - Annotations are passed via `editingEntry?.data?.annotations` in `+page.svelte:2470`, but the `onAnnotationsChange` callback updates only local state without persisting to the server.
   - `handleAiModify` in `PMRichEditor.svelte:228-233` uses `prompt()` for a manual edit instead of calling an AI service; the AI Modify button in `PMAnnotationPanel` calls this handler.

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](data-model.md) for entity definitions.

**No new entities required.** The existing `ModuleEntry` and `EntryAnnotation` types already support the needed fields. The fixes involve:

1. **PMRelationPicker**: Use `getEntries(token, projectId, targetModuleType)` instead of mock data.
2. **PMSpecGlossaryPanel**: Pass `editor` instance from `PMRichEditor` via `+page.svelte`.
3. **Annotations**: Persist annotation changes via `updateEntry()` API; implement actual AI workflow for `handleAiModify`.

### Interface Contracts

No new external interfaces. Existing contracts:

- `getEntries(token, projectId, moduleType?) → ModuleEntry[]` — already implemented
- `updateEntry(token, entryId, data) → ModuleEntry` — already implemented
- `PMRichEditor` props: `annotations`, `onAnnotationsChange` — already defined

### Quickstart

See [quickstart.md](quickstart.md) for validation steps.

---

## Implementation Strategy

### Fix 1: Real Data in PMRelationPicker

**File**: `src/lib/components/pm/PMRelationPicker.svelte`

**Changes**:
- Replace mock data in `loadItems()` with actual `getEntries(token, projectId, targetModuleType)` call
- Add `token` prop or read from `localStorage`
- Handle loading/error states

**Parent wiring** (`+page.svelte`):
- Ensure `PMRelationPicker` is passed `projectId` and receives `onSelect`/`onClear` callbacks
- Verify requirementEntries and parameterEntries are loaded before rendering selectors

### Fix 2: Glossary Panel Insert

**File**: `src/lib/components/pm/PMSpecGlossaryPanel.svelte`

**Changes**:
- No component changes needed — the component already supports `editor` prop

**Parent wiring** (`+page.svelte`):
- Capture `editor` instance from `PMRichEditor` (via `bind:this` or callback)
- Pass `editor` to `PMSpecGlossaryPanel`

### Fix 3: Annotation Sync + AI Modify

**Files**: 
- `src/lib/components/pm/PMRichEditor.svelte`
- `src/lib/components/pm/PMAnnotationPanel.svelte`
- `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`

**Changes**:
- In `+page.svelte`: Update `onAnnotationsChange` to call `updateEntry()` to persist annotations
- In `PMRichEditor.svelte`: Replace `prompt()`-based `handleAiModify` with actual AI workflow (or placeholder that calls AI API)
- Ensure annotation count updates reactively after save

## Success Criteria Verification

| Criterion | How to Verify |
|---|---|
| SC-001: Associate real entities | Open SPEC editor, verify dropdowns show real requirement/parameter entries |
| SC-002: Insert action responds | Click "术语参考" → "插入", verify content appears in editor |
| SC-003: Annotation sync | Add annotation, reload page, verify it persists |
| SC-004: AI Modify triggers | Click "AI修改", verify AI workflow initiates |
| SC-005: No mock data | Verify no "示例条目" or "123测试测试测试" appears |

## Assumptions & Risks

- **Assumption**: `getEntries()` API returns valid data for all target module types (requirement, parameter, etc.)
- **Assumption**: The TipTap editor instance exposes `.chain().focus().insertContent()` API (standard)
- **Risk**: AI Modify requires AI service configuration; if unavailable, must degrade gracefully per Constitution Principle I
- **Risk**: Large entry lists may need pagination/virtualization in PMRelationPicker (future enhancement)
