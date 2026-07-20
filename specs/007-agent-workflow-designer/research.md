# Research: Agent Workflow Designer & Architecture Fix

**Feature**: specs/007-agent-workflow-designer
**Date**: 2026-07-11
**Status**: Complete

## Decisions

### Decision 1: Workflow Node Types

**Decision**: Hybrid mode (pre-defined + custom extension)

**Rationale**: 
- Pre-defined types lower the barrier to entry for common PM workflows
- Custom extensions enable power users to define domain-specific nodes
- Aligns with Constitution §VI (Skill-as-Generic-Module) — custom nodes are registered skills

**Alternatives considered**:
- Fixed types only: Too restrictive for advanced users
- Fully custom: Too complex for PM users who need quick workflow setup

### Decision 2: Workflow Execution Mode

**Decision**: Server-side execution

**Rationale**:
- Data security: PM data (requirements, PRDs) should not be processed in browser
- Complex computation: Agent calls, data transformations require server resources
- State persistence: Execution history needs durable storage
- Error recovery: Server can handle retries, partial state preservation

**Alternatives considered**:
- Client-side: Rejected due to data security and complexity concerns
- Hybrid: Rejected as unnecessary complexity for v1

### Decision 3: Architecture Diagram Fix Scope

**Decision**: Bug fixes only, no new features

**Rationale**:
- User explicitly requested "fix" not "enhance"
- Keeping scope focused prevents feature creep
- Workflow visualization is handled by the dedicated workflow designer

**Alternatives considered**:
- Fix + enhance: Rejected by user preference
- Complete redesign: Out of scope

### Decision 4: Agent Write Confirmation Strategy

**Decision**: Session-level toggle with dangerous-operation override

**Rationale**:
- Balances productivity (no confirmation for every write) with safety (dangerous ops always confirmed)
- "Dangerous" is clearly defined: delete, overwrite
- Future versions can add per-user configuration

**Alternatives considered**:
- All operations require confirmation: Too disruptive
- No confirmation: Violates Constitution §III (Human-Confirmed)

### Decision 5: Workflow Persistence

**Decision**: Definition + complete execution history

**Rationale**:
- PM workflows need audit trails for compliance
- Execution history enables debugging and replay
- History retention policy can limit storage growth

**Alternatives considered**:
- Definition only: Insufficient for PM audit requirements
- Definition + latest state: Misses historical context

## Technology Stack

### Frontend
- **Framework**: SvelteKit (existing Open WebUI architecture)
- **Workflow Canvas**: Svelte Flow / React Flow (via svelte-flow or custom implementation)
- **State Management**: Svelte stores
- **Styling**: Tailwind CSS (existing design system)

### Backend
- **Language**: Python 3.11
- **Framework**: FastAPI (existing Open WebUI API layer)
- **Database**: SQLite (local) / PostgreSQL (production)
- **ORM**: SQLAlchemy (existing)
- **Workflow Engine**: Custom async execution engine

### Integration
- **Agent Framework**: Open WebUI native Tools, Skills, Pipelines
- **PM Module API**: Existing `backend/open_webui/pm/` APIs
- **Skill Registry**: Existing `backend/open_webui/pm/skills/` registry

## Open Questions Resolved

| Question | Answer | Impact |
|----------|--------|--------|
| Node types | Hybrid (pre-defined + custom) | WorkflowNode.type enum, skill registry integration |
| Execution mode | Server-side | Async execution engine, state persistence |
| Architecture diagram scope | Bug fixes only | Limited to existing code fixes |
| Write confirmation | Session toggle + dangerous override | FR-006, confirmation modal logic |
| Persistence scope | Definition + full history | Workflow.execution_history[], retention policy |

## Constraints

- Must conform to Open WebUI's existing architecture (SvelteKit + FastAPI)
- Must follow Constitution §VI (Skill-as-Generic-Module HARD CONSTRAINT)
- Must maintain backward compatibility with existing PM module data
- Must not introduce new auth layer (reuse existing PM permissions)
