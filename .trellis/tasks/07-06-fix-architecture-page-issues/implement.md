## Implementation Plan

### Step 1: Fix Loading Logic

**File**: `src/routes/(app)/pm/[projectId]/architecture/+page.svelte`

- [ ] Replace `Promise.all` with `Promise.allSettled` for better error resilience
- [ ] Ensure `isLoading = false` is always set, even on partial failure
- [ ] Add individual error logging for each API call
- [ ] Test with both APIs succeeding, one failing, and both failing

### Step 2: Fix UI Style

**File**: `src/routes/(app)/pm/[projectId]/architecture/+page.svelte`

- [ ] Identify project's Tab/Button design system (check other pages for patterns)
- [ ] Update Tab button styles to match project conventions
- [ ] Ensure dark mode compatibility

### Step 3: Fix Button Label

**File**: `src/routes/(app)/pm/[projectId]/architecture/+page.svelte`

- [ ] Change "参数详情" to "模块详情"
- [ ] Verify no other references to "参数详情" in this context

### Validation Commands

```bash
# Build check
npm run build

# Lint check
npm run lint

# Type check
npx svelte-check --tsconfig ./tsconfig.json
```

### Rollback Points

- Git commit after each step for easy rollback
- Step 1 and Step 3 are independent and can be rolled back separately
