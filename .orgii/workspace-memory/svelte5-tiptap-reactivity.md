---
name: Svelte 5 + TipTap Reactivity Pattern
description: TipTap Editor is not Svelte-reactive; needs onTransaction + rAF + editor=self-assign to force re-renders. $effect with $state last-value tracking causes infinite loops.
type: feedback
---

When integrating TipTap v3 with Svelte 5 runes, the `Editor` instance is **not a Svelte reactive object**. This means:

1. **Toolbar `editor?.isActive()` calls don't trigger re-renders** — The template reads editor state once but Svelte doesn't know when TipTap's internal state changes. Buttons never update their active/pressed visual state.

2. **The fix: `onTransaction` + rAF + self-assignment pattern** — In the Editor constructor, add `onTransaction` callback that uses `requestAnimationFrame` to reassign `editor = editor`, forcing Svelte to detect a change and re-render:
```svelte
let pendingUpdate = null;
new Editor({
  onTransaction: () => {
    if (!pendingUpdate) {
      pendingUpdate = requestAnimationFrame(() => {
        pendingUpdate = null;
        if (editor && !editor.isDestroyed) {
          editor = editor; // force Svelte re-render
        }
      });
    }
  }
});
```

3. **Never use `$effect` with `$state` last-value tracking for content sync** — The pattern `let lastPropContent = $state(content); $effect(() => { if (content !== lastPropContent) { lastPropContent = content; ... } })` is broken in Svelte 5 because assigning `lastPropContent` inside the effect triggers the same effect to re-run (since `lastPropContent` is a dependency), causing infinite loops or double-execution on every content change. This was the root cause of the blank editor bug.

4. **Always guard with `editor.isDestroyed`** — TipTap editor can be destroyed during component unmount; callbacks that fire after destruction will throw.

5. **Defer `new Editor()` via `requestAnimationFrame`** — When mounting the editor inside `onMount`, wrap the constructor in `requestAnimationFrame(() => { ... })` to ensure the DOM element (`bind:this={element}`) is fully attached before TipTap tries to mount into it. This prevents race conditions where the editor mounts into a detached or unready element.

6. **Remove `prose dark:prose-invert` from editor content div** — The `@tailwindcss/typography` plugin's `.prose` class applies `color: var(--tw-prose-body)` which can override ProseMirror's contenteditable text color, making text invisible in dark mode. Remove these classes from the editor's content container div.

7. **Add `cursor: text` to `.ProseMirror`** — Ensures the cursor shows as a text cursor when hovering over the editor area, improving UX.

8. **Content sync `$effect` refinement** — Read the prop into a local const before comparison: `$effect(() => { const newContent = content; if (newContent !== lastPropContent) { lastPropContent = newContent; ... } })`. This prevents Svelte's reactivity system from tracking the `content` prop access in a way that could cause double-execution.

**Why:** PMRichEditor.svelte had all of these wrong, causing the editor to appear blank and uneditable. The legacy RichTextInput.svelte (Svelte 4) had the correct `onTransaction` + rAF pattern. The Svelte 5 runes rewrite introduced the `$effect`/`$state` last-value anti-pattern. Additionally, the `prose` class from Tailwind Typography was interfering with text visibility.

**How to apply:** When building any TipTap + Svelte 5 component, always use `onTransaction` + rAF for reactivity, never track "last value" with `$state` inside `$effect`. Guard all editor access with `isDestroyed`. Sync `editable` option reactively. Defer init via rAF. Remove `prose` class from the editor content container. Reference the working `RichTextInput.svelte` pattern (but adapted to runes syntax).
