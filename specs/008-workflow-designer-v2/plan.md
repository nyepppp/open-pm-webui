# Implementation Plan: Workflow Designer V2 - Global Access & AI Integration

**Branch**: `[008-workflow-designer-v2]` | **Date**: 2026-07-11 | **Spec**: [specs/008-workflow-designer-v2/spec.md](spec.md)

**Input**: Feature specification from `/specs/008-workflow-designer-v2/spec.md`

## Summary

Implement a visual workflow designer that is globally accessible from the OpenWebUI sidebar (same level as PM Workspace), with AI-assisted generation, comprehensive node library, test-run debugging, and seamless chat integration. The workflow designer supports BPMN/XML and JSON import/export, fixed and custom parameters, and real-time execution trace in both designer and chat contexts.

## Technical Context

**Language/Version**: Python 3.11 (backend), SvelteKit + TypeScript (frontend)

**Primary Dependencies**: 
- Frontend: SvelteKit, Tailwind CSS, xyflow (Svelte Flow for canvas), Lucide icons
- Backend: FastAPI, SQLAlchemy, Pydantic, WebSocket (for execution streaming)
- AI: OpenWebUI existing LLM integration (models, API keys)
- BPMN: xmltodict (XML parsing/generation)

**Storage**: SQLite (local) / PostgreSQL (production) via OpenWebUI's existing ORM

**Testing**: pytest (backend), Vitest (frontend), Playwright (E2E)

**Target Platform**: Web (OpenWebUI extension)

**Project Type**: Web application (frontend + backend)

**Performance Goals**: 
- Workflow designer canvas: 60fps for up to 50 nodes
- AI generation: < 10s for workflows with < 10 nodes
- Execution streaming: < 100ms latency between node updates
- Module switching: < 500ms

**Constraints**:
- Must conform to OpenWebUI Tailwind CSS design system
- Must reuse existing OpenWebUI components (buttons, inputs, modals, dropdowns)
- Dark mode support required
- Responsive layout (desktop primary, tablet secondary)

**Scale/Scope**:
- Support up to 100 nodes per workflow
- Support up to 50 concurrent workflow executions
- Workflow history retention: 30 days

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Constitution v1.2.1 Checklist:**
- [x] Principle I (Manual-First): Feature works without AI / API keys — AI generation is optional; manual node creation always works
- [x] Principle II (Module-Centric): Form fields match business purpose — node parameters are differentiated by type
- [x] Principle III (Human-Confirmed): AI outputs are drafts requiring confirmation — AI-generated workflows require user review before saving
- [x] Principle IV (Data Isolation): `project_id` scoping, no cross-project access — workflows respect project permissions
- [x] Principle V (Version-Controlled): Snapshot, compare, rollback supported — workflow versioning included (FR-021)
- [x] Principle VI (Skill-as-Generic-Module HARD CONSTRAINT): Any agent capability MUST be a `SkillContract` generic module or `pm_*` Tool — custom nodes registered via skill/plugin system
- [x] Deterministic Pipeline Engine: If using Timbal, it MUST be embedded as a Python library, NOT a replacement for Open WebUI native orchestration — execution engine is custom, not Timbal
- [x] Performance: Tool calls ≤3s, RAG ≤1s, module switch ≤500ms — execution streaming < 100ms

**Complexity Tracking**: No violations identified.

## Project Structure

### Documentation (this feature)

```text
specs/008-workflow-designer-v2/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (from /speckit-tasks)
```

### Source Code (repository root)

```text
# Frontend (SvelteKit)
src/
├── routes/
│   ├── (app)/
│   │   ├── workflows/              # Global workflow page (list + designer)
│   │   │   ├── +page.svelte       # Workflow list view
│   │   │   └── [workflowId]/
│   │   │       └── +page.svelte   # Workflow designer
│   │   └── pm/
│   │       └── [projectId]/
│   │           └── workflow/        # Legacy redirect (keep for backward compat)
├── lib/
│   ├── components/
│   │   └── workflow/
│   │       ├── WorkflowDesigner.svelte      # Main designer canvas
│   │       ├── WorkflowNodeSidebar.svelte   # Draggable node palette
│   │       ├── WorkflowCanvas.svelte        # Canvas with nodes/edges
│   │       ├── NodeConfigPanel.svelte     # Node configuration panel
│   │       ├── ExecutionTrace.svelte      # Execution trace viewer
│   │       ├── WorkflowList.svelte        # Workflow list/grid
│   │       ├── WorkflowToolbar.svelte     # Designer toolbar
│   │       ├── AIGenerateModal.svelte     # AI generation modal
│   │       ├── TestRunPanel.svelte        # Test run panel
│   │       └── ChatIntegration.svelte     # Chat integration components
│   ├── stores/
│   │   └── workflowStore.ts       # Workflow state management
│   ├── apis/
│   │   └── workflow/
│   │       ├── index.ts           # API functions
│   │       └── types.ts           # TypeScript types
│   └── utils/
│       └── workflow/
│           ├── bpmnExport.ts      # BPMN/XML export
│           ├── bpmnImport.ts      # BPMN/XML import
│           └── executionEngine.ts # Client-side execution helpers

# Backend (FastAPI)
backend/open_webui/
├── routers/
│   └── workflows.py               # Workflow API endpoints
├── models/
│   └── workflows.py               # SQLAlchemy models
├── services/
│   └── workflow/
│       ├── engine.py              # Workflow execution engine
│       ├── bpmn_converter.py      # BPMN conversion
│       └── ai_generator.py        # AI workflow generation
├── pm/
│   └── skills/
│       └── workflow_nodes.py    # Custom node skill registration
└── migrations/
    └── versions/
        └── add_workflow_tables.py # Database migration
```

**Structure Decision**: Standard OpenWebUI extension pattern — frontend in `src/` (SvelteKit), backend in `backend/open_webui/` (FastAPI). Workflow designer is a standalone feature module, not part of PM workspace.

## Complexity Tracking

> No Constitution violations identified.

| Component | Complexity | Rationale |
|-----------|-----------|-----------|
| Canvas (xyflow) | Medium | Well-documented library, Svelte-compatible |
| Execution Engine | High | Custom engine with streaming, error handling, state management |
| AI Generation | Medium | Reuses existing LLM integration, prompt engineering required |
| BPMN Import/Export | Medium | XML parsing, node mapping, graceful degradation |
| Chat Integration | Medium | Reuses existing chat infrastructure, WebSocket streaming |
| UI Style Alignment | Low | Tailwind CSS, reuse existing components |
