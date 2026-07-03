# Type Safety

> TypeScript type patterns — extracted from `src/lib/apis/pm/types.ts`.

---

## Type Organization

All PM types live in a single file: `src/lib/apis/pm/types.ts`.

**Convention**: Add new types to this file. Don't create separate type files per domain — the PM module is small enough for one file.

---

## Core Type Pattern

```typescript
// Union types for constrained values
export type ModuleType =
    | 'prd'
    | 'requirement'
    | 'parameter'
    | 'testcase'
    | 'risk'
    | 'competitor'
    | 'roadmap'
    | 'meeting'
    | 'acceptance'
    | 'faq'
    | 'product-architecture'
    | 'prototype'
    | 'schedule';

export type ModuleStatus = 'draft' | 'review' | 'approved' | 'archived';
export type Priority = 'p0' | 'p1' | 'p2' | 'p3';

// Interface for data entities
export interface ModuleEntry {
    id: string;
    projectId: string;
    moduleType: ModuleType;
    title: string;
    content?: string;
    metadata?: Record<string, unknown>;
    versionId?: string;
    status: ModuleStatus;
    priority?: Priority;
    currentVersionNumber?: string;
    branchName?: string;
    createdAt: number;
    updatedAt: number;
    version: number; // optimistic lock
}
```

---

## FieldConfig Type

Form field definitions use a discriminated union via `type`:

```typescript
export interface FieldConfig {
    name: string;
    label: string;
    type: 'text' | 'textarea' | 'select' | 'date' | 'number' | 'combobox' | 'multiselect';
    required?: boolean;
    options?: string[];
    validation?: { min?: number; max?: number; pattern?: string };
    placeholder?: string;
    dependsOn?: string;       // for cascading selects
    dataSource?: string;      // for combobox data source
}
```

---

## API Response Types

API functions in `version.ts` and `relation.ts` use inline generic types:

```typescript
export function compareEntryVersions(projectId: string, entryId: string, versionA: string, versionB: string) {
    return getOne<{
        contentDiff: { path: string; type: 'added' | 'removed' | 'modified'; old: unknown; new: unknown }[];
        metadataDiff: { field: string; old: unknown; new: unknown }[];
    }>(`/projects/${projectId}/entries/${entryId}/versions/compare?versionA=${versionA}&versionB=${versionB}`);
}
```

**Convention**: For simple responses, inline the type. For complex/reused responses, define an interface in `types.ts`.

---

## Validation

- **Runtime**: `PMFormEditor` validates based on `FieldConfig.required` and `FieldConfig.validation`.
- **No Zod in components** — Zod is installed but not used in PM components currently. `FieldConfig` drives validation.
- **Backend**: Pydantic models handle server-side validation.

---

## Common Patterns

1. **`Record<string, unknown>`** for flexible metadata/data fields.
2. **Optional fields use `?`** — `content?: string`.
3. **Timestamps are `number`** — Epoch milliseconds (matching backend `BigInteger`).
4. **Union types for enums** — Not TypeScript `enum`.

---

## Forbidden Patterns

1. **`any`** — Use `unknown` and narrow with type guards.
2. **Type assertions without checks** — Don't use `as ModuleType` on untrusted data; validate first.
3. **Duplicating backend type names** — Frontend types use camelCase (`projectId`), backend uses snake_case (`project_id`). The API boundary handles the mapping.
