# Hook Guidelines

> Data fetching and lifecycle patterns — extracted from actual PM components.

---

## Data Fetching Pattern

No custom hooks are used. Data fetching follows a **load-on-mount** pattern:

```svelte
<script lang="ts">
    import { onMount } from 'svelte';

    let items = $state<ModuleEntry[]>([]);
    let loading = $state(false);
    let error = $state('');

    onMount(async () => {
        loading = true;
        try {
            items = await getEntries(token, projectId, moduleType);
        } catch (e) {
            error = e.message;
        } finally {
            loading = false;
        }
    });
</script>
```

**Convention**: No React-style custom hooks (`useXxx`). Svelte 5 uses `$state` + `onMount` + async functions.

---

## Effect Patterns

### Reacting to prop changes

```svelte
$effect(() => {
    // React to projectId change
    if (projectId) {
        loadData(projectId);
    }
});
```

### Reacting to URL params

```svelte
<script lang="ts">
    import { page } from '$app/stores';
    let projectId = $derived($page.params.projectId);
    let moduleType = $derived($page.params.module as ModuleType);
</script>
```

### Cleanup

```svelte
$effect(() => {
    const observer = new ResizeObserver(...);
    observer.observe(element);
    return () => observer.disconnect();
});
```

---

## Toast Notifications

Use `svelte-sonner` for user feedback:

```svelte
import { toast } from 'svelte-sonner';

// Success
toast.success('条目已保存');

// Error
toast.error('保存失败: ' + error.message);
```

---

## Navigation

Use SvelteKit's `$app/stores` and `goto`:

```svelte
import { goto } from '$app/navigation';
import { page } from '$app/stores';

// Read params
let projectId = $derived($page.params.projectId);

// Navigate
function navigateToEntry(moduleType: string, entryId: string) {
    goto(`/pm/${projectId}/${moduleType}?entryId=${entryId}`);
}
```

---

## Common Mistakes

1. **Not using `onMount` for initial data fetch** — Component renders before data loads; show loading state.
2. **$effect without cleanup** — ResizeObserver, event listeners, and intervals must be cleaned up.
3. **Direct DOM manipulation** — Use Svelte reactivity instead of `document.querySelector`.
4. **Fetching in `$effect` without guard** — Use `if (projectId)` to prevent fetch with undefined params.
