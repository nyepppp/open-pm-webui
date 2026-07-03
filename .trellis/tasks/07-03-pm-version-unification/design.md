# PM模块富文本编辑与文档导入修复 — Technical Design

## Architecture Overview

2 bugs, 1 component layer, 1 page layer:

```
Bug 1: Rich text editor not editable
  PMRichEditor.svelte → TipTap Editor init → ProseMirror view
  Root causes:
    A) Svelte template nesting error in +page.svelte — {:else} block at L1895
       renders PMRichEditor but the closing + next {:else if} at L1917 is
       misaligned, belonging to a DIFFERENT {#if} block (edit drawer).
       This causes Svelte to misinterpret the template tree, potentially
       preventing the editor from mounting or receiving props correctly.
    B) PMRichEditor onMount uses requestAnimationFrame to defer init — if the
       element is unmounted/remounted due to the template error, the rAF
       callback fires on a stale element.
    C) CSS: ProseMirror sets `outline: none` and `cursor: text` but no
       `pointer-events` issue found — however parent containers with
       `overflow: hidden` or incorrect z-index could block clicks.

Bug 2: Document import not working
  PMDocumentImporter.svelte → file input → mammoth/marked → editor.setContent
  Root causes:
    A) PMDocumentImporter only renders when `editor` is not null (L78: {#if editor}).
       If Bug 1 prevents editor init, the import button disappears entirely.
    B) In +page.svelte, there is a SEPARATE import path via hidden <input type="file">
       and `onMdFileSelected` handler. The `marked.parse()` call was missing `await`
       (now fixed). But this path only handles .md files, not .docx or .txt.
    C) PMDocumentImporter uses `editor.commands.setContent(html, true)` — the second
       arg `true` is deprecated in TipTap v2+. Should be `{ emitUpdate: true }`
       or omitted (defaults to true).
```

## Bug 1: Rich text editor not editable

### Fix A: Svelte template nesting in `+page.svelte`

**Problem**: At L1917, `{:else if moduleType === 'prototype'}` appears to be a continuation of the entry editor view's if/else chain (which has `{:else if isMindmapView}` at L1874 and `{:else}` at L1895). However, L1917 actually belongs to the **edit drawer** if/else block that starts at a different level. The missing `{/if}` to close the entry editor view's if/else chain causes Svelte to misparse the template.

**Fix**: Verify the exact if/else block boundaries and ensure the entry editor view's if/else chain is properly closed with `{/if}` before the edit drawer's `{:else if moduleType === 'prototype'}` branch.

**Investigation needed**: Read lines 1600–1960 of `+page.svelte` to trace the full `{#if}` / `{:else if}` / `{/if}` structure and identify exactly where the missing close tag is.

### Fix B: PMRichEditor initialization hardening

Already applied in previous session:
- Added `initError` state and error logging in `onMount`
- Added `onCreate`/`onDestroy` callbacks for lifecycle tracking
- Added `editorReady` state for external consumers
- Improved initialization guard (check element before and after rAF)

**No further changes needed** for this sub-fix unless the template nesting fix reveals additional issues.

### Fix C: CSS pointer-events verification

**Investigation needed**: Check if any parent container in `+page.svelte` sets `pointer-events: none` or uses an overlay that intercepts clicks before they reach the ProseMirror editor.

The PMRichEditor's own CSS is clean:
- `.ProseMirror { outline: none; cursor: text; }` — correct
- No `pointer-events: none` anywhere in the component

## Bug 2: Document import not working

### Fix A: PMDocumentImporter rendering depends on editor

**Current behavior**: `{#if editor}` at L78 of PMDocumentImporter.svelte means the import button only shows when the TipTap editor is initialized.

**This is correct behavior** — the importer needs the editor to call `setContent`. The real fix is ensuring Bug 1 is resolved so the editor initializes successfully.

### Fix B: Separate import path in +page.svelte

**Already fixed**: Added `await` to `marked.parse(text)` call in `onMdFileSelected`.

**Remaining issue**: The separate import path in `+page.svelte` only handles `.md` files. The `PMDocumentImporter` component handles all three formats (.md, .docx, .txt). These two paths should be consolidated or the page-level path should be removed in favor of the component.

**Decision**: Keep both paths for now. The page-level hidden `<input>` is used for drag-and-drop and quick import from the entry list. The component-level importer is for the rich editor toolbar. They serve different UX flows. Just ensure both work correctly.

### Fix C: PMDocumentImporter setContent call

**Current**: `editor.commands.setContent(html, true)` at L62

**Fix**: Change to `editor.commands.setContent(html, { emitUpdate: true })` for TipTap v2+ type safety. This matches the fix already applied to PMRichEditor.svelte's setContent call.

## Implementation Order

```
1. Fix Svelte template nesting in +page.svelte (Bug 1 Fix A)
   → This unblocks both the editor and the importer
2. Fix PMDocumentImporter setContent call (Bug 2 Fix C)
   → Type safety fix, quick
3. Verify CSS pointer-events (Bug 1 Fix C)
   → Investigation only, likely no change needed
4. Test end-to-end
   → Editor editable + all 3 import formats work
```

## Rollback

All changes are frontend-only:
- Revert `+page.svelte` template structure fix
- Revert `PMDocumentImporter.svelte` setContent call
- Revert `PMRichEditor.svelte` initialization hardening (already applied)

Files affected:
- `src/routes/(app)/pm/[projectId]/[module]/+page.svelte`
- `src/lib/components/pm/PMDocumentImporter.svelte`
- `src/lib/components/pm/PMRichEditor.svelte`
