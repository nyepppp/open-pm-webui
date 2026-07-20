# Implementation Plan: PM Skills Integration

**Branch**: `[003-pm-skills-integration]` | **Date**: 2026-07-11 | **Spec**: [specs/003-pm-skills-integration/spec.md](specs/003-pm-skills-integration/spec.md)

**Input**: Feature specification from `/specs/003-pm-skills-integration/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Integrate the pm-skills repository (68+ PM skills) into the Open WebUI PM workspace as reusable SkillContract modules. Enable users to invoke pm-skills commands via `/pm-<id>` or have the Agent autonomously load relevant methodologies. Skills are stored locally, mapped to SkillContracts, and invoked through Timbal Workflows embedded as Python library within Open WebUI backend.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript/SvelteKit (frontend)

**Primary Dependencies**: 
- **Timbal** (`pip install timbal`) — Workflow engine (embedded as Python library, NOT independent service)
- Open WebUI native skill system
- Existing PM module infrastructure

**Storage**: SQLite (local) / PostgreSQL (production) via Open WebUI's ORM

**Testing**: pytest (backend), Playwright (frontend E2E)

**Target Platform**: Open WebUI web application

**Project Type**: Web application (Open WebUI extension)

**Performance Goals**: Tool calls ≤ 3s, skill loading ≤ 1s, workflow execution ≤ 5s

**Constraints**: 
- Must conform to Open WebUI architecture
- **Timbal embedded as Python library** (NOT independent service, NOT `timbal start`)
- All skills must be SkillContract modules
- No hidden magic: async functions + Pydantic validation + event-driven streaming

**Scale/Scope**: 68+ skills, multiple concurrent users, per-project isolation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Constitution v1.2.1 Checklist:**
- [x] Principle I (Manual-First): Feature works without AI / API keys — pm-skills can be invoked manually via `/pm-<id>` commands
- [x] Principle II (Module-Centric): Skills are generic modules, not bound to specific PM features
- [x] Principle III (Human-Confirmed): All write operations require `requiresConfirm=True`
- [x] Principle IV (Data Isolation): All operations scoped by `project_id`
- [x] Principle V (Version-Controlled): pm-skills versions pinned, mappings versioned
- [x] Principle VI (Skill-as-Generic-Module HARD CONSTRAINT): All pm-skills are SkillContract modules registered in unified registry
- [x] Deterministic Pipeline Engine: Timbal used only as embedded Python library for deterministic workflows
- [x] Performance: Tool calls ≤3s, skill loading ≤1s

## Project Structure

### Documentation (this feature)

```text
specs/003-pm-skills-integration/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
backend/open_webui/pm/
├── skills/
│   ├── pm-skills/           # Local copy of pm-skills repository
│   │   ├── pm-product-discovery/
│   │   ├── pm-product-strategy/
│   │   ├── pm-execution/
│   │   └── ...
│   ├── base.py              # BaseSkill with outputContract support
│   ├── __init__.py          # Unified skill registry
│   └── pm_skills_loader.py  # pm-skills loading and mapping
├── workflows/
│   └── pm_skills_workflow.py  # Timbal Workflow definitions (embedded Python library)
├── timbal_config.py         # Timbal configuration (model settings, fallback)
└── tools.py                 # pm_* Tools for skill invocation

src/lib/components/pm/
├── SkillPanel.svelte        # Skill selection UI
└── WorkflowBuilder.svelte     # Workflow configuration UI
```

**Structure Decision**: Extend existing Open WebUI PM module structure. pm-skills stored as local files under `backend/open_webui/pm/skills/pm-skills/`. Skills registered in unified registry. Timbal Workflows embedded as Python library (`import timbal`) within Open WebUI backend — NOT as independent service (`timbal start`).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | — | — |
