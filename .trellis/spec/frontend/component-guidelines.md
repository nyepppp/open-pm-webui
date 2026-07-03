# Component Guidelines

> How components are built — extracted from `src/lib/components/pm/`.

---

## Svelte 5 Runes Pattern

All PM components use Svelte 5 runes syntax:

```svelte
<script lang="ts">
    interface Props {
        content?: string;
        onChange?: (content: string) => void;
        readonly?: boolean;
    }

    let { content = '', onChange, readonly = false }: Props = $props();

    let editor: Editor | null = $state(null);
    let loading = $state(false);
    let items = $derived(items.filter(i => i.active));
</script>
```

**Convention**:
- Use `$props()` with interface — NOT `export let`.
- Use `$state()` for reactive local state.
- Use `$derived()` for computed values.
- Use `$effect()` for side effects (with cleanup return).

---

## Component Structure

Every component follows this order:

```svelte
<script lang="ts">
    // 1. Imports
    import { onMount } from 'svelte';
    import type { ModuleEntry } from '$lib/apis/pm/types';

    // 2. Props interface + destructuring
    interface Props { ... }
    let { ... }: Props = $props();

    // 3. Local state ($state)
    let loading = $state(false);

    // 4. Derived state ($derived)
    let filteredItems = $derived(items.filter(...));

    // 5. Effects ($effect)
    $effect(() => { ... return () => cleanup(); });

    // 6. Functions
    async function loadData() { ... }

    // 7. Lifecycle (onMount)
    onMount(() => { ... });
</script>

<!-- Template -->
<div>...</div>

<!-- No <style> blocks — use Tailwind utility classes -->
```

---

## Props Conventions

1. **Always use `interface Props`** — Define props with a TypeScript interface.
2. **Destructure with defaults** — `let { readonly = false, onChange }: Props = $props();`
3. **Callback props use `on` prefix** — `onChange`, `onSelect`, `onDelete`, `onNavigate`.
4. **Optional props have defaults** — Never leave optional props without defaults.

---

## Styling Patterns

- **Tailwind CSS only** — No `<style>` blocks, no CSS modules, no styled-components.
- **Dark mode** — Always provide `dark:` variants: `bg-white dark:bg-gray-900`.
- **Common patterns**:

```html
<!-- Card -->
<div class="rounded-xl border border-gray-200 dark:border-gray-700 p-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">

<!-- Badge -->
<span class="text-xs px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">

<!-- Status indicator -->
<span class="inline-block w-2.5 h-2.5 rounded-full bg-yellow-400">
```

---

## Editor Components

PM has three editor types, each as a standalone component:

| Component | Use For | Key Props |
|-----------|---------|-----------|
| `PMRichEditor` | Rich text (PRD, meeting) | `content`, `onChange`, `readonly`, `showToc` |
| `PMFormEditor` | Structured forms (risk, FAQ) | `fields`, `data`, `onChange`, `onSubmit` |
| `PMMixedEditor` | Form + rich text (risk, competitor) | `fields`, `content`, `onChange` |

The module page (`[module]/+page.svelte`) selects the editor based on `moduleConfig[moduleType].editorType`.

---

## Common Mistakes

1. **Using `export let`** — Must use `$props()` in Svelte 5.
2. **Missing `dark:` variants** — All text and background classes need dark mode.
3. **Inline styles** — Use Tailwind classes, never `style="..."`.
4. **Not passing `onChange` callbacks** — Always propagate state changes upward.
