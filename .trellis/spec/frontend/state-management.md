# State Management

> How state is managed — extracted from `src/lib/stores/pm/`.

---

## State Categories

| Category | Mechanism | When to Use |
|----------|-----------|-------------|
| Component-local | `$state()` | Form data, UI toggles, loading/error |
| Component-derived | `$derived()` | Filtered lists, computed flags |
| Cross-component | Svelte `writable` stores | Project, version, module selection |
| URL state | `$page.params` / `$page.url.searchParams` | projectId, moduleType, entryId |

---

## Svelte Store Pattern

For state shared across components (project context, version list), use Svelte stores:

```typescript
// versionStore.ts
import { writable, derived, type Writable, type Readable } from 'svelte/store';

// State
export const versions: Writable<Version[]> = writable([]);
export const currentVersion: Writable<Version | null> = writable(null);
export const versionLoading: Writable<boolean> = writable(false);
export const versionError: Writable<string | null> = writable(null);

// Derived
export const sortedVersions: Readable<Version[]> = derived(
    versions,
    $versions => [...$versions].sort((a, b) => b.createdAt - a.createdAt)
);

// Actions
export function setVersions(versionList: Version[]) {
    versions.set(versionList);
}

export function addVersion(version: Version) {
    versions.update(list => [...list, version]);
}

export function resetVersionStore() {
    versions.set([]);
    currentVersion.set(null);
    versionLoading.set(false);
    versionError.set(null);
}
```

**Convention**:
- Each store file exports writable atoms, derived reads, and action functions.
- Action functions use `.set()` or `.update()` — never mutate store value directly.
- Always export a `reset*Store()` function.

---

## Local State Pattern

For component-only state, use Svelte 5 runes:

```svelte
<script lang="ts">
    let loading = $state(false);
    let error = $state('');
    let formData = $state<Record<string, unknown>>({ ...data });
    let showPanel = $state(false);
</script>
```

**Convention**: Use `$state()` for all local reactive state. Use plain `let` for non-reactive values (e.g., `let lastPropContent = content`).

---

## Derived State Pattern

```svelte
<!-- In components -->
let filteredItems = $derived(items.filter(i => i.active));

<!-- In stores -->
export const filteredVersions: Readable<Version[]> = derived(
    [sortedVersions, versionSearchQuery],
    ([$sorted, $query]) => {
        if (!$query.trim()) return $sorted;
        return $sorted.filter(v => v.versionNumber.toLowerCase().includes($query.toLowerCase()));
    }
);
```

---

## When to Use Global State

Promote state to a Svelte store when:

1. **Multiple components need it** — Current project, current version.
2. **It persists across route changes** — Project context survives navigation.
3. **It needs derived computations** — Filtered/sorted lists.

Keep state local when:

1. **Only one component uses it** — Form data, loading flags.
2. **It resets on unmount** — Dialog visibility, edit mode.
3. **It's URL-derived** — Use `$page.params` instead.

---

## Common Mistakes

1. **Using `$state` for cross-component state** — Use Svelte stores instead.
2. **Not resetting stores** — Always export and call `reset*Store()` on project change.
3. **Mutating store value directly** — Use `.set()` or `.update()`.
4. **Duplicating URL state in stores** — If it's in `$page.params`, don't also store it.
