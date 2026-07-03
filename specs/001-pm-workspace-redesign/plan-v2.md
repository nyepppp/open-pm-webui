# Implementation Plan: PM 工作台增强 v2

**Created**: 2026-06-29
**Status**: Draft

---

## Technical Context

| Item | Value |
|------|-------|
| Frontend Framework | SvelteKit (Svelte 5) |
| UI Library | Tailwind CSS + bits-ui + OpenWebUI shared components |
| Rich Text Editor | TipTap v3 (fully installed with extensions) |
| Flow/Diagram | @xyflow/svelte ^0.1.19 (溯源图) |
| Mind Map | mind-elixir (NEEDS INSTALL) |
| Gantt Chart | frappe-gantt ^1.2.2 (installed) |
| Calendar | OpenWebUI built-in (CalendarView, CalendarEventModal, API) |
| Document Parsing | mammoth ^1.12.0 (.docx), marked ^9.1.0 (.md) |
| Validation | zod ^4.4.3 |
| Date | dayjs ^1.11.10 |
| Charts | chart.js ^4.5.0, mermaid ^11.10.1 |

---

## Constitution Check

| Principle | Compliance | Notes |
|-----------|-----------|-------|
| I. Manual-First | ✅ | 所有版本操作、溯源连线、日程同步均可手动触发 |
| II. Module-Centric | ✅ | 各模块差异化字段补全，编辑器类型不变 |
| III. AI-Assisted, Human-Confirmed | ✅ | 溯源连线手动确认，版本合并手动解决冲突 |
| IV. Data Isolation & Traceability | ✅ | 条目版本按 projectId 隔离，溯源图支持双向追溯 |
| V. Version-Controlled Documentation | ✅ | 新增条目级版本、分支、合并，嵌入编辑页面 |

---

## Complexity Tracking

| Area | Complexity | Justification |
|------|-----------|---------------|
| 版本比较 | HIGH | 需要递归比较 TipTap JSON 节点差异，高亮显示 |
| 版本合并 | HIGH | 三路对比 + 冲突检测 + 解决界面 |
| 溯源连线交互 | MEDIUM | xyflow 原生支持 onConnect，需自定义 UI 层 |
| 思维导图 | MEDIUM | mind-elixir 集成 + 数据格式转换 |
| 甘特图 | LOW | frappe-gantt 已安装，封装即可 |
| 日程集成 | LOW | OpenWebUI 日历 API 完备，调用即可 |
| 文档导入 | LOW | mammoth/marked 已安装，TipTap 支持 HTML 注入 |
| 自动目录 | LOW | TipTap heading 提取，实现简单 |

---

## Phase 0: Setup & Dependencies

### T001 [P] Install mind-elixir
- `npm install mind-elixir`
- Verify TypeScript types available

### T002 [P] Create database migration for new tables
- `pm_entry_versions`, `pm_version_branches`, `pm_version_merges`, `pm_schedule_syncs`
- Add columns to `pm_module_entries`: `current_version_id`, `current_version_number`, `branch_name`
- Migrate existing entries: create initial EntryVersion for each

### T003 [P] Update TypeScript types
- Add EntryVersion, VersionBranch, VersionMerge, ScheduleSync types to `src/lib/apis/pm/types.ts`
- Add new API functions to version.ts, relation.ts

---

## Phase 1: US1 — 条目版本直显 (P1)

### T004 [US1] Add version badge to PM item cards
- Modify `[module]/+page.svelte` item list rendering
- Display `currentVersionNumber` as badge (blue solid for current, gray outline for historical)
- Click badge → dropdown showing version history for that entry

### T005 [US1] Create PMVersionHistoryDropdown.svelte
- Fetches EntryVersion list for a given entryId
- Shows version number, changeSummary, createdAt
- Click version → load that version's content

---

## Phase 2: US2 — 版本比较·合并·分支 (P1)

### T006 [P] [US2] Create PMVersionComparePanel.svelte (inline panel)
- Embedded in document editing page (not a dialog)
- Left/right split view
- Content diff: compare TipTap JSON nodes, highlight additions (green) / deletions (red)
- Metadata diff: table showing field-level differences
- For each diff: "Keep Old" / "Keep New" / "Manual Edit" buttons

### T007 [US2] Implement TipTap JSON diff algorithm
- Recursive comparison of ProseMirror document nodes
- Mark added/deleted/modified nodes with attributes
- Render diff highlights in the compare panel

### T008 [US2] Create PMVersionBranchDialog.svelte
- Input: branch name
- Creates VersionBranch record from current entry version
- Switches editor to branch context

### T009 [US2] Create PMVersionMergePanel.svelte
- Shows branch vs main differences
- Auto-detects conflicts
- Conflict resolution UI: side-by-side with resolution options
- "Merge" button → creates merged EntryVersion on main branch

### T010 [US2] Integrate version controls into module editor page
- Add "Compare Versions" button → opens PMVersionComparePanel
- Add "Create Branch" button → opens PMVersionBranchDialog
- Add "Merge Branch" button → opens PMVersionMergePanel
- Show current branch indicator in editor header

---

## Phase 3: US3 — 富文本统一 & 文档导入 & 自动目录 (P1)

### T011 [P] [US3] Unify TipTap configuration across all rich text modules
- Define PM_TIPTAP_EXTENSIONS constant (all extensions)
- Update PMRichEditor.svelte to use unified config
- Verify all rich modules (prd, competitor, meeting, faq, acceptance, roadmap) use same config

### T012 [P] [US3] Create PMDocumentImporter.svelte
- File input: accept .docx, .md, .txt
- .docx: mammoth → HTML → editor.commands.setContent()
- .md: marked → HTML → editor.commands.setContent()
- .txt: plain text insert
- Import full document text, not chapters
- Add "Import Document" button to PMRichEditor toolbar

### T013 [P] [US3] Create PMTableOfContents.svelte
- Accept TipTap editor instance as prop
- Listen to editor update events
- Extract all heading nodes (H1-H6)
- Render collapsible tree with level indentation
- Click item → scroll to heading position
- Real-time update on heading changes

### T014 [US3] Integrate TOC into PMRichEditor
- Add TOC panel as sidebar in the rich text editor layout
- Show/hide TOC toggle button in toolbar
- Responsive: hide TOC on narrow screens

---

## Phase 4: US10 — 溯源交互增强 (P1)

### T015 [P] [US10] Enable xyflow connection line in PMTraceabilityGraph
- Add connection line support (drag from port to port)
- Configure onConnect callback
- Show available source/target ports on nodes

### T016 [US10] Create PMRelationTypeSelector.svelte
- Modal/dropdown for selecting relation type
- Types: contains, references, derives, modifies, conflicts
- On select → call relation.create API
- On success → add edge to graph + update module form

### T017 [US10] Create PMTraceDetailPanel.svelte
- Side panel showing entity details
- Loads full entry data when node clicked
- Inline editing for key fields
- Shows upstream/downstream relations

### T018 [US10] Add right-click context menu on edges
- Custom context menu component
- Options: Change Relation Type, Delete Relation, View Impact Analysis
- Change type → dropdown selector → update API
- Delete → confirm dialog → delete API
- Impact analysis → navigate to PMImpactAnalysisView

### T019 [US10] Add double-click navigation on nodes
- Double-click node → navigate to /pm/{moduleType}?entryId={id}
- Open entry in edit mode

### T020 [US10] Sync trace links to module form fields
- When relation created via trace graph → update corresponding relation fields in module form
- When relation deleted via trace graph → remove from module form
- Use relation store for bidirectional sync

---

## Phase 5: US4 — 日程与产品工作目录打通 (P2)

### T021 [P] [US4] Create PMCalendarSync service
- On PM entry save (roadmap milestone, risk deadline, schedule task) → call calendar API to create/update event
- Map: pmEntityId → calendarEventId stored in ScheduleSync table
- Handle sync failures with retry queue

### T022 [US4] Integrate calendar event creation in roadmap/schedule/risk modules
- After saving entry with dates → trigger calendar sync
- Show sync status indicator on entry

### T023 [US4] Create PMScheduleOverview.svelte
- Fetch PM-related calendar events for current week/month
- Display as compact list in PM sidebar or header
- Click event → navigate to PM module entry

### T024 [US4] Add PM link handling in CalendarView
- When calendar event has PM data in meta field → show "Go to PM" link
- Click → navigate to PM module with entry highlighted

---

## Phase 6: US8 — 甘特图统一 (P2)

### T025 [P] [US8] Create PMGanttChart.svelte (shared component)
- Wraps frappe-gantt
- Props: tasks (GanttTask[]), viewMode, onDateChange, onProgressChange, onClick
- Support: drag to resize, drag to move, dependency arrows
- Styling: match OpenWebUI theme

### T026 [US8] Integrate Gantt in roadmap module
- Add "Timeline" view tab alongside mind map view
- Convert roadmap entries → GanttTask format
- Bidirectional: drag in gantt → update entry dates

### T027 [US8] Integrate Gantt in schedule module
- Create schedule module if not exists
- Default view: Gantt chart + task list
- Tasks sync with calendar (via Phase 5)

---

## Phase 7: US9 — 思维导图 & 产品架构 (P2)

### T028 [P] [US9] Create PMMindMapEditor.svelte (mind-elixir wrapper)
- Initialize mind-elixir with Svelte container element
- Bridge: mind-elixir data ↔ PM backend format
- Support: add/delete/edit nodes, drag, collapse/expand
- Custom node rendering: show PM entity icon and version badge

### T029 [US9] Replace PMMindMap.svelte with mind-elixir version
- Update roadmap module to use PMMindMapEditor
- Update product-architecture module to use PMMindMapEditor
- Keep @xyflow/svelte for PMTraceabilityGraph (different use case)

### T030 [US9] Add auto-extract for product architecture
- "Extract from modules" button → scan PRD, requirements, parameters
- Generate mind map nodes from module structure
- User can confirm/adjust extracted nodes

---

## Phase 8: US5, US6, US7 — 功能完善 & 复用 (P2)

### T031 [US5] Update moduleFields.ts with missing fields per PRD
- Competitor: add analysis dimensions table field
- FAQ: change answer to rich text editor type
- Risk: add matrix probability/impact fields
- All modules: add traceability relation fields where missing

### T032 [US6] Add PRD check module
- Create PMPrdCheckPanel.svelte
- Define check rules (L1-L4 levels)
- Run checks and display results

### T033 [US7] Identify and integrate OpenWebUI shared components
- File upload → reuse existing component
- Document preview → reuse existing viewer
- Ensure calendar components reused (Phase 5)

### T034 [US6] Add missing modules from PRD
- Schedule/排期 module (with gantt from Phase 6)
- Deliverable/交付物料 module (checklist)
- Issue/问题闭环 module (tracker)
- Retrospective/版本复盘 module

---

## Phase 9: Polish & Integration Testing

### T035 Verify version badge display on all 11+ modules
### T036 Verify version compare works with all content types
### T037 Verify branch/merge with concurrent edits
### T038 Verify document import preserves formatting
### T039 Verify TOC auto-updates on heading changes
### T040 Verify calendar sync bidirectional
### T041 Verify Gantt chart in roadmap and schedule
### T042 Verify mind map in roadmap and product-architecture
### T043 Verify trace graph interaction (connect, click, right-click, double-click)
### T044 Performance test: 50+ gantt tasks, 200+ mind map nodes, 100+ trace nodes

---

## Dependencies & Execution Order

```
Phase 0 (Setup) ←── blocks all
    │
    ├─→ Phase 1 (Version Display) ←── independent
    ├─→ Phase 2 (Version Compare/Merge/Branch) ←── depends on Phase 0
    ├─→ Phase 3 (Rich Text + Import + TOC) ←── independent
    ├─→ Phase 4 (Trace Interaction) ←── independent
    │
    ├─→ Phase 5 (Calendar Integration) ←── after Phase 0
    ├─→ Phase 6 (Gantt Chart) ←── after Phase 0
    ├─→ Phase 7 (Mind Map) ←── after Phase 0
    ├─→ Phase 8 (Feature Completion) ←── after Phase 3, 4
    │
    └─→ Phase 9 (Polish) ←── after all above
```

**Parallel opportunities**:
- Phases 1, 3, 4 can run in parallel (no dependencies between them)
- Phases 5, 6, 7 can run in parallel after Phase 0
- Phase 8 depends on Phases 3+4 but parts can start earlier

---

## Task Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 0: Setup | T001-T003 | Dependencies, DB migration, types |
| Phase 1: US1 | T004-T005 | Version badge display |
| Phase 2: US2 | T006-T010 | Version compare/merge/branch |
| Phase 3: US3 | T011-T014 | Rich text unified + import + TOC |
| Phase 4: US10 | T015-T020 | Trace interaction enhancement |
| Phase 5: US4 | T021-T024 | Calendar integration |
| Phase 6: US8 | T025-T027 | Gantt chart unified |
| Phase 7: US9 | T028-T030 | Mind map + product architecture |
| Phase 8: US5/6/7 | T031-T034 | Feature completion + reuse |
| Phase 9: Polish | T035-T044 | Integration testing |

**Total Tasks**: 44
**P1 Tasks (Phases 0-4)**: 20
**Estimated Duration**: 3-4 weeks (P1), 6-8 weeks (full)
