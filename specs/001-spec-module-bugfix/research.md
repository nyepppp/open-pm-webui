# Research: SPEC Module Bug Fixes

**Date**: 2026-07-10
**Feature**: SPEC Module Bug Fixes
**Spec**: [spec.md](spec.md)

## Decision: Use Existing `getEntries` API for Real Data

**Rationale**: The `getEntries(token, projectId, moduleType)` API in `src/lib/apis/pm/index.ts:137-149` already supports fetching entries by module type. It is used successfully in other modules (testcase, requirement-boundary) to populate dropdowns. No new API is needed.

**Alternatives considered**:
- Create a new `getModuleList` API — rejected: unnecessary duplication, `getEntries` already covers this
- Use a separate relation API — rejected: over-engineering for this bug fix, relations can be stored in entry `data` field

## Decision: Pass Editor Instance via Props for Glossary Insert

**Rationale**: `PMSpecGlossaryPanel` already accepts an `editor` prop and has the correct `insertTerm` logic. The parent `+page.svelte` simply needs to pass the editor instance. This is the minimal change.

**Alternatives considered**:
- Use Svelte context/store for editor — rejected: unnecessary complexity, direct prop passing is cleaner
- Refactor to event-based communication — rejected: over-engineering for a simple insert action

## Decision: Persist Annotations via `updateEntry` API

**Rationale**: Annotations are currently stored in `editingEntry.data.annotations` but only updated in local state. The existing `updateEntry(token, entryId, data)` API can persist the updated annotation array. This matches how other module data is saved.

**Alternatives considered**:
- Create a dedicated annotation API — rejected: annotations are part of entry data, no need for separate endpoint
- Use WebSocket for real-time sync — rejected: out of scope for bug fix, polling/reload is acceptable

## Decision: AI Modify Uses Existing AI Chat Infrastructure

**Rationale**: The project already has `PMAgentChatPanel` and AI integration. For the AI Modify button, the simplest fix is to open the agent chat with the annotation content pre-filled, or to use the existing AI suggestion flow. If AI is unavailable, show a clear message.

**Alternatives considered**:
- Implement inline AI editing in the annotation panel — rejected: too complex for a bug fix
- Use a separate AI endpoint — rejected: existing agent chat infrastructure is sufficient

## Key Code References

| File | Line | Issue |
|---|---|---|
| `PMRelationPicker.svelte` | 66-92 | Mock data in `loadItems()` |
| `PMSpecGlossaryPanel.svelte` | 23-27 | `editor` prop not passed |
| `PMRichEditor.svelte` | 228-233 | `handleAiModify` uses `prompt()` |
| `+page.svelte` | 2442-2455 | `onAnnotationsChange` not persisted |

## No Backend Changes Required

All fixes are frontend-only. The existing API layer (`getEntries`, `updateEntry`) supports the required operations.
