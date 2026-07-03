---
name: Svelte 5 class attribute syntax — inline ternary expressions invalid
description: Svelte 5 does not support inline ternary expressions inside class attributes. Use class: directives instead.
type: feedback
---

**Rule:** In Svelte 5, never use inline ternary expressions inside `class` attributes (e.g., `class="... {condition ? 'a' : 'b'}"`). This syntax is invalid and causes build errors.

**Why:** Svelte 5 changed how class attributes are handled. Inline JavaScript expressions in class strings are no longer supported. The compiler throws a syntax error.

**How to apply:**
- Replace inline ternary in class strings with Svelte 5 `class:` directives.
- Example (invalid):
  ```svelte
  <button class="base {active ? 'bg-blue-600' : 'bg-white'}">
  ```
- Example (valid):
  ```svelte
  <button class="base" class:bg-blue-600={active} class:bg-white={!active}>
  ```
- This was fixed in `PMVersionCreateDialog.svelte` where a complex inline ternary with dark mode variants caused the build to fail.