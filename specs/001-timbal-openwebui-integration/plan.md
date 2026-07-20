# Implementation Plan: Timbal-OpenWebUI Integration

**Branch**: `[001-timbal-openwebui-integration]` | **Date**: 2026-07-12 | **Spec**: [specs/001-timbal-openwebui-integration/spec.md](specs/001-timbal-openwebui-integration/spec.md)

**Input**: Feature specification from `/specs/001-timbal-openwebui-integration/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Implement a comprehensive Timbal-OpenWebUI integration that enables workflow execution, PM workspace tool exposure, visual workflow designer, and chat-based invocation. The integration supports multiple invocation protocols (REST, SSE, WebSocket), bidirectional data flow, and Git-style versioning. Key technical decisions include using a plugin bridge for extensibility, automatic + manual + template-driven parameter mapping for PM data, and multi-format result rendering.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript/SvelteKit (frontend)

**Primary Dependencies**: FastAPI, SvelteFlow, Timbal API, OpenWebUI existing stack

**Storage**: SQLite (local) / PostgreSQL (production) via OpenWebUI ORM

**Testing**: pytest (backend), Vitest (frontend), Playwright (E2E)

**Target Platform**: Web application (OpenWebUI extension)

**Project Type**: Web application (frontend + backend integration)

**Performance Goals**: <5s for simple workflow execution, <1s SSE latency, <3s PM tool response

**Constraints**: Must integrate with existing OpenWebUI auth, must not break existing PM workspace functionality

**Scale/Scope**: Single-instance deployment, supports concurrent workflow executions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Constitution Compliance Review

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Manual-First Productivity | ✅ PASS | Workflows can be created and executed manually without AI assistance |
| II. Module-Centric Architecture | ✅ PASS | Workflow module is independent of PM workspace; nodes map to PM operations |
| III. AI-Assisted, Human-Confirmed | ✅ PASS | AI-generated workflows are suggestions; human confirms before execution |
| IV. Data Isolation & Traceability | ✅ PASS | Each execution has isolated ID; execution logs preserve traceability |
| V. Version-Controlled Documentation | ✅ PASS | Git-style versioning for workflows with full history |

### Complexity Tracking

> No Constitution violations detected. All principles are satisfied by the current design.

## Project Structure

### Documentation (this feature)

```text
specs/001-timbal-openwebui-integration/
├── spec.md              # Feature specification (/speckit-specify output)
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
backend/
├── open_webui/
│   ├── pm/
│   │   └── timbal_config.py       # Timbal configuration settings
│   └── routers/
│       └── timbal.py              # Timbal API routes
├── lib/
│   └── timbal/
│       ├── client.py              # Timbal API client
│       ├── models.py              # Timbal data models
│       └── tools.py               # PM tool definitions
└── tests/
    └── timbal/
        └── test_integration.py

src/
├── lib/
│   ├── apis/
│   │   └── timbal/                # Timbal API client (Svelte)
│   │       ├── index.ts
│   │       └── types.ts
│   └── components/
│       └── timbal/
│           ├── WorkflowDesigner.svelte
│           ├── WorkflowNode.svelte
│           └── WorkflowExecution.svelte
├── routes/
│   └── (app)/
│       └── workflows/
│           ├── +page.svelte
│           └── [workflowId]/
│               └── +page.svelte
└── stores/
    └── timbalStore.ts
```

**Structure Decision**: Option 2 (Web application with backend + frontend). The backend extends OpenWebUI's existing FastAPI structure with Timbal-specific routes and models. The frontend uses SvelteKit with SvelteFlow for the visual designer, matching OpenWebUI's existing architecture.

## Phase 0: Research

See [research.md](research.md) for detailed findings.

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| Plugin bridge for OpenWebUI integration | Enables extensibility without modifying core OpenWebUI code; follows OpenWebUI's existing plugin architecture |
| SvelteFlow for visual designer | Already used in OpenWebUI; minimal learning curve; supports custom node types |
| Git-style versioning | Provides full audit trail; supports branching for draft workflows |
| Exponential backoff for retries | Industry standard; prevents thundering herd |
| Open permissions model | Matches user's explicit choice; simplifies initial implementation |

### Technology Choices

| Technology | Purpose | Alternative Considered |
|------------|---------|------------------------|
| FastAPI + httpx | Timbal API client | aiohttp (more complex, no benefit) |
| SvelteFlow | Visual workflow designer | React Flow (requires React, not Svelte) |
| SSE | Real-time status updates | WebSocket (overkill for one-way updates) |
| JSON Schema | Input/output validation | Protocol Buffers (too heavy for this use case) |

## Phase 1: Design

### Data Model

See [data-model.md](data-model.md) for full entity definitions.

### Interface Contracts

See [contracts/](contracts/) for API contracts.

### Quickstart

See [quickstart.md](quickstart.md) for validation scenarios.

## Next Steps

1. Review and approve this plan
2. Run `/speckit-tasks` to generate implementation tasks
3. Begin implementation following the tasks
