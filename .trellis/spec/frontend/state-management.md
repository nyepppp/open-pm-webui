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

---

## Version ID Resolution Pattern

When resolving a version display from a module entry, always follow this chain:

```svelte
<!-- Table column: currentVersionNumber -->
{@const cvn = entry.currentVersionNumber}
{@const entryVid = entry.versionId || getEntryData(entry, 'versionId')}
{@const isUuid = cvn && /^[0-9a-f]{8}-/i.test(String(cvn))}
{@const resolvedVid = isUuid ? cvn : entryVid}
{@const matchedVersion = resolvedVid ? $versionList.find((v: any) => v.id === resolvedVid) : null}
{@const displayVn = matchedVersion ? (matchedVersion.versionNumber || matchedVersion.version_number) : (!isUuid && cvn ? cvn : '')}
```

```svelte
<!-- Card badge: versionId -->
{@const cardVersionId = getEntryData(entry, 'versionId') || entry.versionId || (entry.currentVersionNumber && /^[0-9a-f]{8}-/i.test(String(entry.currentVersionNumber)) ? entry.currentVersionNumber : '')}
{@const cardVersion = cardVersionId ? $versionList.find((v: any) => v.id === cardVersionId) : null}
{cardVersion?.versionNumber || cardVersion?.version_number || '-'}
```

**Resolution chain** (in priority order):
1. `getEntryData(entry, 'versionId')` — from `entry.data.versionId` or `entry.metadata.versionId` (JSON column)
2. `entry.versionId` — top-level field (may be undefined if backend doesn't return it)
3. `entry.currentVersionNumber` — if it's a UUID format, use as versionId lookup

**Display fallback**: Always use `versionNumber || version_number` since the API field name varies between `versionNumber` (camelCase) and `version_number` (snake_case).

### Don't: Only check one source for version ID

```svelte
// Bad — only checks currentVersionNumber, shows UUID or '-' when empty
{@const displayVn = entry.currentVersionNumber}
```

```svelte
// Bad — only checks data.versionId, misses entries with UUID in currentVersionNumber
{@const vid = getEntryData(entry, 'versionId')}
{@const vn = vid ? $versionList.find(v => v.id === vid)?.versionNumber : null}
```

### handleCreate: Always persist versionId in data

For `handleCreate`, ensure `data.data.versionId` is set for **all** module types, including rich editor types (meeting, prd) that don't set `data.data` in their module-specific blocks:

```typescript
const currentVer = $currentVersion;
if (currentVer?.id) {
    data.versionId = currentVer.id;
    if (data.data && typeof data.data === 'object') {
        (data.data as Record<string, unknown>).versionId = currentVer.id;
    } else {
        data.data = { versionId: currentVer.id };
    }
}
```

**Why**: The top-level `data.versionId` is silently discarded by the backend (not in `PMEntryForm`). Version association is persisted through `data.data.versionId` (JSON column), which is what `getEntryData()` reads.
