# Workspace Memory Index

## PM Module
- [pm-v5-architecture-goals](pm-v5-architecture-goals.md) — User's 6-point mandate for PM workspace deep integration and completion — highest execution approval granted
- [pm-v5-bug-batch](pm-v5-bug-batch.md) — 2026-07-13: All 8 Vibe annotation issues fixed (workflows, mindmap, traceability, flowchart, version display, home page)
- [planner-mode-activation](planner-mode-activation.md) — 5-phase PM module implementation plan approved 2026-07-03; 7 tasks created and assigned
- [pm-planner-execution-progress](pm-planner-execution-progress.md) — 2026-07-03 sde-tester verdict FAILED: P0 metadata-column bug still on disk despite "rework completed" claim; 138 PM frontend TS errors, no Alembic migrations, no PM tests
- [pm-v4-bug-batch](pm-v4-bug-batch.md) — 18 Vibe annotations → spec at specs/002-pm-v4-bugfix/spec.md → root causes confirmed for all P0/P1 bugs; implementation plan created with 11 tasks
- [pm-backend-version-apis](pm-backend-version-apis.md) — Backend database tables and API endpoints for entry-level versioning (snapshots, branches, merges)
- [pm-v2-enhancement-progress](pm-v2-enhancement-progress.md) — Tracks v2 and v3 spec feature implementation status — what's done and what remains
- [pm-module-500-error](pm-module-500-error.md) — PM module 500 error from Svelte 4 event syntax and missing API exports; ALL FIXES APPLIED AND BUILD VERIFIED

## Technical Notes
- [svelte5-tiptap-reactivity](svelte5-tiptap-reactivity.md) — TipTap Editor is not Svelte-reactive; needs onTransaction + rAF + editor=self-assign to force re-renders. $effect with $state last-value tracking causes infinite loops.
- [svelte5-event-syntax](svelte5-event-syntax.md) — Svelte 4→5 migration: event modifiers and on: directives are invalid; use callback props and e.stopPropagation() instead
- [shell-windows-escaping](shell-windows-escaping.md) — Windows shell tool mangles double-quoted strings with semicolons; use single quotes or alternative approaches
- [sqlalchemy-reserved-metadata](sqlalchemy-reserved-metadata.md) — Never name a Column `metadata` on Declarative Base; use `info`/`vmetadata`/`meta` per repo convention

## User Preferences
- [user-pm-preferences](user-pm-preferences.md) — User's preferences for PM module UX and feature priorities, observed from Vibe annotations