# Quality Guidelines

> Code quality standards for frontend development — extracted from actual code patterns.

---

## Required Patterns

1. **Svelte 5 runes** — Use `$props()`, `$state()`, `$derived()`, `$effect()`. No `export let`.
2. **TypeScript strict** — All components must have `lang="ts"` in `<script>`.
3. **Props interface** — Always define `interface Props` for component props.
4. **Error state** — Always handle `loading`, `error`, and `empty` states in data-fetching components.
5. **Dark mode** — All visible elements must have `dark:` Tailwind variants.

---

## Forbidden Patterns

1. **`export let`** — Use `$props()` in Svelte 5.
2. **`<style>` blocks** — Use Tailwind CSS utility classes only.
3. **`any` type** — Use specific types from `types.ts` or `unknown`.
4. **Inline `fetch()` without error handling** — Always wrap in try/catch.
5. **`document.querySelector`** — Use Svelte reactivity or `bind:this`.

---

## API Client Pattern

All API calls go through the helper functions in `$lib/apis/pm/index.ts`:

```typescript
// Good — uses typed helper
import { getEntries, createEntry } from '$lib/apis/pm/index';

// Good — uses domain-specific API file
import { createEntryVersion } from '$lib/apis/pm/version';

// Bad — raw fetch without error handling
const res = await fetch('/api/v1/pm/projects');
```

---

## Form Validation Pattern

`PMFormEditor` validates using `FieldConfig` metadata:

```typescript
interface FieldConfig {
    name: string;
    label: string;
    type: 'text' | 'textarea' | 'select' | 'date' | 'number' | 'combobox' | 'multiselect';
    required?: boolean;
    options?: string[];
    validation?: { min?: number; max?: number; pattern?: string };
    placeholder?: string;
    dependsOn?: string;
    dataSource?: string;
}
```

**Convention**: New module fields must be added to `moduleFields.ts` with proper `FieldConfig` entries.

---

## Code Review Checklist

- [ ] Component uses `$props()` not `export let`
- [ ] All props have TypeScript types
- [ ] Loading/error/empty states handled
- [ ] Dark mode variants present
- [ ] API calls use helper functions from `$lib/apis/pm/`
- [ ] No inline styles — Tailwind only
- [ ] New module fields defined in `moduleFields.ts`
- [ ] Store state reset on navigation
