# Frontend Development Guidelines

> Best practices for frontend development — extracted from actual code patterns.

---

## Overview

The frontend is a **SvelteKit (Svelte 5)** application with **Tailwind CSS** and **bits-ui** components. The PM module demonstrates all core patterns: API layer, stores, components, routing, and form handling.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Module organization and file layout | ✅ Documented |
| [Component Guidelines](./component-guidelines.md) | Svelte 5 runes, props, composition | ✅ Documented |
| [Hook Guidelines](./hook-guidelines.md) | Data fetching, effects, lifecycle | ✅ Documented |
| [State Management](./state-management.md) | Svelte stores, runes, derived state | ✅ Documented |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, forbidden patterns | ✅ Documented |
| [Type Safety](./type-safety.md) | TypeScript types, validation | ✅ Documented |

---

## How These Were Created

Each guideline was extracted by inspecting the actual codebase — `src/lib/components/pm/`, `src/lib/apis/pm/`, `src/lib/stores/pm/`, and `src/routes/(app)/pm/`. No aspirational patterns are included; only patterns with existing code examples.

---

**Language**: All documentation should be written in **English**.
