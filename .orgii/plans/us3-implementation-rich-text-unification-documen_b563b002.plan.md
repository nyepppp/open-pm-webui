# US3 Implementation: 富文本统一·文档导入·自动目录

## Context

The PM module currently has a minimal TipTap rich text editor (`PMRichEditor.svelte`) with only StarterKit + Placeholder extensions and a basic toolbar (bold, italic, heading, lists). The module page (`[module]/+page.svelte`) uses OpenWebUI's `RichTextInput` for PRD editing and inline editing logic for other modules. All rich-text modules should have identical capabilities. Document import currently splits by chapters instead of importing full text. There's no auto-generated table of contents from headings.

**Available TipTap extensions** (all installed in package.json):
- StarterKit, Image, Link, Table, CodeBlock (lowlight), Highlight, List, Mention, Placeholder, Typography, YouTube, BubbleMenu, FloatingMenu, DragHandle, FileHandler

**Available document parsing libraries** (installed):
- `mammoth ^1.12.0` (.docx → HTML)
- `marked ^9.1.0` (.md → HTML)

## Approach

### Step 1: Create unified TipTap extension configuration (`src/lib/components/pm/pmTiptapConfig.ts`)

Extract a shared `PM_TIPTAP_EXTENSIONS` array containing all installed extensions with their configurations. This becomes the single source of truth for all rich text editors in PM modules. Include:
- StarterKit (paragraph, heading levels 1-6, bold, italic, strike, code, codeBlock, blockquote, horizontalRule, hardBreak)
- Image, Link, Table (with TableRow, TableCell, TableHeader)
- CodeBlockLowlight, Highlight, List (BulletList, OrderedList), Typography
- Mention, Placeholder, YouTube
- BubbleMenu, FloatingMenu

### Step 2: Upgrade PMRichEditor.svelte with full extensions and enhanced toolbar

Replace the minimal 5-button toolbar with a comprehensive toolbar matching all PM_TIPTAP_EXTENSIONS capabilities. Add toolbar sections:
- **Text**: Bold, Italic, Strike, Highlight colors
- **Headings**: H1-H6 dropdown
- **Lists**: Bullet, Ordered, Task list
- **Insert**: Image, Link, Table, Code block, YouTube
- **Structure**: Blockquote, Horizontal rule
- **Utility**: Undo, Redo, Import Document, Toggle TOC

Add the `editor` instance as an exported ref so PMTableOfContents can access it.

### Step 3: Create PMDocumentImporter.svelte

A toolbar-embedded component that accepts a TipTap editor instance. When triggered:
- Opens a file picker (.docx, .md, .txt)
- .docx: uses `mammoth` to convert to HTML, then `editor.commands.setContent(html)`
- .md: uses `marked` to convert to HTML, then `editor.commands.setContent(html)`
- .txt: inserts as plain text paragraphs
- Imports **full document text** (not chapter-by-chapter)

### Step 4: Create PMTableOfContents.svelte

A sidebar component that accepts a TipTap `Editor` instance as prop. Works by:
- Listening to editor `onUpdate` events
- Extracting all heading nodes (H1-H6) from the ProseMirror document
- Rendering a collapsible tree with indentation by level
- Click on a TOC item → `editor.chain().focus().scrollToHeading(id).run()` or manual scroll
- Real-time updates when headings change
- Highlight current heading based on scroll position

### Step 5: Integrate TOC + Importer into PMRichEditor layout

Refactor PMRichEditor.svelte to have:
- A layout with optional TOC sidebar (left) + editor content (right)
- TOC toggle button in toolbar (show/hide sidebar)
- Import Document button in toolbar (opens PMDocumentImporter)
- Responsive: TOC sidebar hidden on screens < 1024px

### Step 6: Update module page to use upgraded PMRichEditor for all rich-text modules

In `[module]/+page.svelte`, ensure all modules with `editorType: 'rich'` (prd, competitor, meeting, faq) and `editorType: 'mixed'` (risk, acceptance) use the upgraded PMRichEditor with full extensions. The module page already imports `RichTextInput` for PRD; unify to use PMRichEditor consistently.

## Key Files

| File | Change |
|------|--------|
| `src/lib/components/pm/pmTiptapConfig.ts` | **NEW** — Shared TipTap extension config array |
| `src/lib/components/pm/PMRichEditor.svelte` | **REWRITE** — Full toolbar, unified extensions, TOC sidebar layout, import button |
| `src/lib/components/pm/PMDocumentImporter.svelte` | **NEW** — File picker + mammoth/marked conversion |
| `src/lib/components/pm/PMTableOfContents.svelte` | **NEW** — Auto TOC from headings |
| `src/lib/components/pm/PMMixedEditor.svelte` | **UPDATE** — Pass unified config to PMRichEditor |
| `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` | **UPDATE** — Use PMRichEditor for all rich/mixed modules, remove RichTextInput import for PRD editing |

## Risks & Open Questions

1. **TipTap v3 compatibility**: Some extensions like DragHandle, FileHandler require specific TipTap v3 setup. Need to verify they work with `@tiptap/core ^3.0.7`.
2. **mammoth browser usage**: mammoth is primarily a Node.js library but has browser compatibility. Need to verify it works in SvelteKit client-side context without Node fs module.
3. **PMRichEditor vs RichTextInput**: The module page currently uses OpenWebUI's `RichTextInput` for PRD editing. Unifying to PMRichEditor means all rich text uses the same component, but we need to verify PMRichEditor handles all the same features (markdown rendering, code highlighting).
4. **TOC scroll sync**: TipTap doesn't have a built-in `scrollToHeading` command. Need to implement scroll-to-heading by finding the DOM element with the heading's position and scrolling the editor container.
