# Quickstart: PM 工作台增强 v2

**Created**: 2026-06-29

---

## Prerequisites

- OpenWebUI dev server running (`npm run dev`)
- PM module accessible at `/pm`
- At least one PM project created with entries in multiple modules

---

## Validation Scenarios

### V1: 条目版本直显

1. Navigate to `/pm/prd`
2. Verify each entry card/row shows a version badge (e.g., "v1.0")
3. Click the version badge → dropdown shows version history
4. Select a different version → entry content updates

**Pass criteria**: Version badges visible on all module entry lists

### V2: 版本比较

1. Open a PRD entry with multiple versions
2. Click "Compare Versions" button in editor
3. Select two versions to compare
4. Verify left/right split view with highlighted differences
5. Click a difference → verify resolution options appear

**Pass criteria**: Diff highlights visible, resolution options work

### V3: 版本分支与合并

1. Open an entry, click "Create Branch"
2. Enter branch name, confirm
3. Edit content in branch → save
4. Switch to main branch → verify branch edits not visible
5. Click "Merge Branch" → verify conflict detection
6. Resolve conflicts → merge

**Pass criteria**: Branch isolation works, merge with conflict resolution works

### V4: 富文本统一

1. Open competitor analysis module → create/edit entry
2. Verify toolbar has same buttons as PRD module (image, table, code block, etc.)
3. Repeat for FAQ, meeting minutes modules

**Pass criteria**: All rich text modules have identical toolbar

### V5: 文档导入

1. Open PRD editor → click "Import Document" in toolbar
2. Upload a .docx file with headings, bold, lists, tables
3. Verify full document text imported (not split by chapters)
4. Verify formatting preserved (headings, bold, lists)

**Pass criteria**: Full text imported with ≥85% format retention

### V6: 自动目录

1. Open PRD editor with content containing H1-H3 headings
2. Verify TOC panel appears in sidebar
3. Click TOC item → scrolls to heading
4. Add a new H2 heading → verify TOC updates automatically

**Pass criteria**: TOC auto-generates and updates in real-time

### V7: 日程集成

1. Create a roadmap milestone with start/end dates
2. Navigate to Calendar page (`/calendar`)
3. Verify milestone appears as calendar event
4. Click event → verify "Go to PM" link works
5. Check PM sidebar schedule overview

**Pass criteria**: Milestone syncs to calendar, bidirectional navigation works

### V8: 甘特图

1. Open roadmap module → switch to "Timeline" view
2. Verify Gantt chart renders with task bars
3. Drag a task bar → verify dates update
4. Open schedule module → verify same Gantt component

**Pass criteria**: Gantt renders, drag works, component consistent across modules

### V9: 思维导图

1. Open roadmap module → mind map view
2. Add a child node → verify appears
3. Drag node to reposition → verify works
4. Collapse/expand nodes → verify works
5. Open product-architecture module → verify mind map view

**Pass criteria**: Mind map CRUD and drag work, consistent across modules

### V10: 溯源交互

1. Open traceability graph for a project
2. Drag from node A's port to node B → verify relation type selector appears
3. Select relation type → verify edge created and relation API called
4. Single-click a node → verify detail panel opens with editable fields
5. Right-click an edge → verify context menu (change type, delete, impact analysis)
6. Double-click a node → verify navigation to module editor
7. Check module form → verify relation field auto-updated

**Pass criteria**: All trace interactions work, bidirectional sync with forms
