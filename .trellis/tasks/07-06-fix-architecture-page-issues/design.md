## Technical Design

### Problem Analysis

1. **Loading Issue**
   - Root cause: `loadData()` in `+page.svelte` fetches both `parameter` and `product-architecture` entries simultaneously via `Promise.all`
   - If either API call fails or hangs, `isLoading` remains `true`
   - No timeout handling or partial failure recovery

2. **UI Style Inconsistency**
   - Current Tab buttons use custom inline styles: `bg-blue-600`, `bg-gray-100`, etc.
   - Project likely has a design system with standardized button/Tab components
   - Need to identify and use existing design tokens

3. **Label Mismatch**
   - Simple string change: "参数详情" → "模块详情"
   - Need to verify this change doesn't break other references

### Solution Approach

1. **Loading Fix**
   - Add individual error handling for each API call
   - Set `isLoading = false` even on partial failure
   - Add timeout or use `Promise.allSettled` for better resilience

2. **UI Style Fix**
   - Search for existing Tab/Button components in the project
   - Apply consistent styling using project's Tailwind classes

3. **Label Fix**
   - Direct string replacement in `+page.svelte`

### Data Flow

```
+page.svelte (loadData)
  ├── getEntries(token, projectId, 'parameter') → parameterEntries
  └── getEntries(token, projectId, 'product-architecture') → archEntries
       
+page.svelte (render)
  ├── Tab: "架构图" → PMMindMap (archEntries)
  └── Tab: "模块详情" → ModuleFeatureTree + ParameterTable (parameterEntries)
```

### Risk Assessment

- **Low risk**: Label change is straightforward
- **Medium risk**: Loading logic change may affect error states
- **Low risk**: UI style change is cosmetic
