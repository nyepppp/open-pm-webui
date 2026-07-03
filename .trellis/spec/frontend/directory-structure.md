# Directory Structure

> How frontend code is organized — extracted from actual code patterns.

---

## PM Module Layout

```
src/
├── lib/
│   ├── apis/pm/                # API client layer
│   │   ├── index.ts            # Base HTTP helpers (getOne, create, update, remove) + project/entry CRUD
│   │   ├── types.ts            # Shared TypeScript types
│   │   ├── version.ts          # Version/branch/merge API calls
│   │   ├── relation.ts         # Relation/traceability API calls
│   │   ├── agent.ts            # Agent API calls
│   │   ├── agentChat.ts        # Agent chat API
│   │   ├── agentTools.ts       # Agent tool API
│   │   ├── analysisService.ts  # Analysis service
│   │   └── modules/            # Per-module API files
│   │       ├── prd.ts
│   │       ├── requirement.ts
│   │       └── ...
│   ├── components/pm/          # PM UI components
│   │   ├── PMRichEditor.svelte       # TipTap rich text editor
│   │   ├── PMFormEditor.svelte       # Structured form editor
│   │   ├── PMMixedEditor.svelte      # Form + rich text hybrid
│   │   ├── PMMindMap.svelte          # @xyflow/svelte diagram
│   │   ├── PMTraceabilityGraph.svelte
│   │   ├── PMVersionCompareDialog.svelte
│   │   ├── moduleFields.ts           # Per-module field definitions
│   │   ├── pmTiptapConfig.ts         # TipTap extension config
│   │   └── pmAnnotationExtension.ts  # Custom TipTap extension
│   └── stores/pm/              # Svelte stores
│       ├── projectStore.ts
│       ├── versionStore.ts
│       ├── moduleStore.ts
│       ├── agentStore.ts
│       └── agentChatStore.ts
└── routes/(app)/pm/            # SvelteKit routes
    ├── +layout.svelte              # PM layout (sidebar + header)
    ├── +page.svelte                # Project list
    ├── [projectId]/
    │   ├── +layout.svelte          # Project layout
    │   ├── +page.svelte            # Project overview
    │   ├── [module]/+page.svelte   # Module page (main editor)
    │   ├── versions/+page.svelte   # Version management
    │   └── traceability/+page.svelte  # Traceability graph
```

---

## Naming Conventions

| Category | Convention | Example |
|----------|-----------|---------|
| Components | `PM` prefix + PascalCase | `PMRichEditor.svelte` |
| API files | camelCase | `version.ts`, `agentChat.ts` |
| Store files | camelCase + `Store` suffix | `versionStore.ts` |
| Types file | `types.ts` | Shared across all PM modules |
| Route params | camelCase | `[projectId]`, `[module]` |

---

## Key Conventions

1. **PM prefix** — All PM-specific components use the `PM` prefix to avoid collision with OpenWebUI core components.
2. **API layer separation** — Base HTTP helpers in `index.ts`, domain APIs in separate files. Domain APIs import from `index.ts`.
3. **One store per domain** — `projectStore.ts`, `versionStore.ts`, etc. Each manages a single concern.
4. **Route structure mirrors domain** — `/pm/[projectId]/[module]` for module editing, `/pm/[projectId]/traceability` for the graph view.
