---
name: PM Enhancement Progress
description: Tracks v2 and v3 spec feature implementation status — what's done and what remains
type: workspace
---

The v2 spec (spec-v2.md / plan-v2.md) defines 44 tasks across 9 phases. A v3 plan was created on 2026-07-01 covering 9 Vibe annotation fixes — **all v3 items are now implemented**.

**v2 Completed (implemented in code):**
- Phase 0 T002/T003: ModuleEntry new fields, EntryVersion, VersionBranch, ConflictItem, VersionMerge types; version.ts API extended
- Phase 1 US1 (条目版本直显): PMVersionHistoryDropdown badge on all module cards
- Phase 2 US2 (版本比较·合并·分支): PMVersionComparePanel, PMVersionBranchDialog, PMVersionMergePanel, auto-version on save
- Phase 3 US3 (富文本统一·文档导入·自动目录): PMRichEditor, PMDocumentImporter, PMTableOfContents
- Phase 4 US10 (溯源交互增强): PMTraceabilityGraph with xyflow connections, PMRelationTypeSelector, PMTraceDetailPanel

**v2 NOT yet implemented:**
- Phase 0 T001: mind-elixir not installed
- Phase 5 US4 (日程打通): T021-T024 — calendar sync
- Phase 6 US8 (甘特图统一): T025-T027 — PMGanttChart shared component
- Phase 7 US9 (思维导图): T028-T030 — PMMindMapEditor with mind-elixir
- Phase 8 US5/6/7 (功能完善): T031-T034
- Phase 9 Polish: T035-T044

**v3 Implemented (2026-07-01) — all 9 items done:**
1. ✅ Fix "创建于 Invalid Date" — shared `pmTimeUtils.ts` with null/0/undefined guards; replaced normalizeTs in 4 files; conditional rendering hides invalid dates
2. ✅ Version Git化 — version card is now clickable `<a>` linking to `/pm/{id}/versions`; versions page already existed with branch/compare placeholders
3. ✅ AI与OpenWebUI打通 — agentChatStore now has `sendViaOpenWebUI()` fallback using `generateOpenAIChatCompletion`; model selector dropdown in chat panel; config link to `/workspace/models` when unconfigured; AI status card shows OpenWebUI model availability
4. ✅ 参数层级选择 — FieldConfig type extended with `combobox`, `dataSource`, `dependsOn`; parameterFields use `moduleName`/`featureName` combobox with module→feature cascade; datalist-backed `<input>` renderer added
5. ✅ PRD整文导入 — onMdFileSelected now injects full HTML directly into editingContentHtml, no chapter splitting
6. ✅ 移除PRD章节大纲 — removed `w-56` sidebar with 章节大纲 from PRD editor; PMTableOfContents component kept for potential reuse
7. ✅ 思维导图数据持久化 — PMMindMap onChange now maps nodes back to source entries via nodeToEntry map, calls `updateEntry` for each, then `loadEntries()` to refresh
8. ✅ 路线图时间维度 — added ganttTimeScale (day/week/month) and ganttViewOffset state; toggle buttons 天/周/月 with ◀/今天/▶ navigation; each row shows durationDays + description snippet; "今天" red marker line; column headers adapt to scale

**Key new files created:**
- `src/lib/utils/pmTimeUtils.ts` — shared normalizeTs/formatDate/formatDateTime

**Key files modified:**
- `src/lib/stores/pm/agentChatStore.ts` — OpenWebUI integration, model selection
- `src/lib/components/pm/PMAgentChatPanel.svelte` — model selector, config link
- `src/lib/apis/pm/types.ts` — FieldConfig combobox/dataSource/dependsOn
- `src/lib/components/pm/moduleFields.ts` — parameter cascade fields
- `src/routes/(app)/pm/+page.svelte` — normalizeTs fix, conditional date rendering
- `src/routes/(app)/pm/[projectId]/+page.svelte` — normalizeTs fix, AI card enhancement, version card link
- `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` — normalizeTs fix, PRD import, outline removal, mindmap save, gantt time dimensions, combobox renderer
- `src/routes/(app)/pm/[projectId]/versions/+page.svelte` — normalizeTs fix, formatDateTime usage

**v3 Plan created (2026-07-02) — 4 major themes, not yet implemented:**

Theme A: **Version tracking globalized** — all module lists need filtering (version/status/priority/source), sorting (by date/priority/version), pagination (pageSize=20). Table views need version column added. Traceability graph needs version-aware filtering and version badges on nodes. Relations should store version snapshots.

Theme B: **Rich text editor customization + version system** — Manual save creates new EntryVersion (user confirms); auto-save (30s debounce) updates content without version bump. Editor header shows version number + save status. Compare panel: rewrite to side-by-side with red/green diff (Myers algorithm + line-level highlight + synced scroll). Merge panel: rewrite to 3-column layout with line-level/multi-line conflict resolution. Annotation feature: TipTap custom Mark (highlight yellow), selection→popup→annotate, annotation list sidebar panel, AI-assisted annotation modification (call OpenWebUI chat API to suggest edits on annotated text). New types: EntryAnnotation. New files: pmAnnotationExtension.ts, PMAnnotationPanel.svelte, PMSaveVersionDialog.svelte, pmDiff.ts.

Theme C: **PRD document sync & verification** — Audit all FR-001 to FR-027 against current implementation, mark implemented/partial/not-implemented. Verify traceability graph connections actually create Relation records. Verify version badges on ALL module views (table rows currently missing). Verify rich text uniformity across all modules. Write manual test checklist.

Theme D: **Traceability enhancement** — Nodes show version badges. Filter bar: module type, version, relation type. Connection creation auto-records version snapshot. Detail panel shows full version history.

**v4 Bugfix (2026-07-02) — ALL DONE (11/11):**
Spec at `specs/002-pm-v4-bugfix/spec.md` with 11 user stories.
- P0 (3/3 ✅): TipTap editor fix, version badge readonly, project data isolation
- P1 (4/4 ✅): Version compare panel (created from scratch), parameter cascade, architecture mindmap, prototype module
- P2 (4/4 ✅): Roadmap today marker, schedule form fields, style consistency, calendar sync
See `pm-v4-bug-batch.md` for full implementation details.

**v4 Key Refinement (2026-07-02):**
The version badge fix evolved during implementation: instead of adding a `readonly` prop to `PMVersionHistoryDropdown`, the table/card rows now use plain `<span>` badges that look up `entry.data.versionId` against `$versionList` to display the creation version. This is simpler and more robust than the dropdown component approach. The `PMVersionHistoryDropdown` component was kept but its `readonly` prop is no longer used in list views.

**TipTap Fix Refined (2026-07-02):**
Additional fixes discovered during final verification:
- Remove `prose dark:prose-invert` Tailwind class from editor content div — it interferes with ProseMirror contenteditable
- Defer `new Editor()` via `requestAnimationFrame` to ensure DOM is fully ready before TipTap mounts
- Add `cursor: text` and `color: inherit` CSS to `.ProseMirror` for better UX
- The `$effect` content sync was further refined to read `content` into a local const before comparison, preventing reactivity issues

**Why:** User observed that many features diverge from PRD, version compare/merge are placeholder-level, entries lack filtering/sorting/paging, and annotation/批注 is a new high-value feature request.

**How to apply:** When implementing next, start with Theme A (filtering/sorting/paging) as foundation for all lists, then Theme B (editor customization + annotation + compare/merge rewrite) as highest user value, then Theme C (audit) for quality, then Theme D (traceability polish). The v3 spec and plan should be created as `spec-v3.md` and `plan-v3.md` under `specs/001-pm-workspace-redesign/`. For v4 bugfix, implement P0 tasks first (TipTap fix → data isolation → version badge readonly), then P1, then P2.
