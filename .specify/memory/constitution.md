<!--
  Sync Impact Report
  Version change: 0.0.0 → 1.0.0
  Added sections:
    - I. Manual-First Productivity
    - II. Module-Centric Architecture
    - III. AI-Assisted, Human-Confirmed
    - IV. Data Isolation & Traceability
    - V. Version-Controlled Documentation
    - Additional Constraints (Tech Stack)
    - Development Workflow
  Removed sections: None (first ratification)
  Templates requiring updates:
    ✅ .specify/templates/plan-template.md — Constitution Check section updated
    ✅ .specify/templates/spec-template.md — User scenarios aligned with principles
    ✅ .specify/templates/tasks-template.md — Task categorization reflects module-driven workflow
    ✅ .specify/templates/checklist-template.md — No changes needed
  Follow-up TODOs:
    - TODO(RATIFICATION_DATE): Confirm actual project start date with team
    - TODO(CONSTITUTION_VERSION): Minor bump expected after Phase 1 completion
-->

# PM Workflow Platform Constitution

## Core Principles

### I. Manual-First Productivity

Every feature MUST support pure manual operation without AI assistance. AI is an accelerator, never a requirement.

- All 10 PM modules (PRD, requirements, parameters, test cases, risks, competitors, roadmap, meetings, acceptance, FAQ) MUST be fully functional via manual data entry
- Form fields, table editing, and document creation MUST work without API keys configured
- AI-generated content MUST be presented as suggestions requiring explicit user confirmation before persistence
- The platform MUST remain a complete PM tool when offline or when AI services are unavailable

**Rationale**: Product managers cannot afford workflow disruption when AI services fail, rate-limit, or produce incorrect output. Manual-first ensures the tool is always operational.

### II. Module-Centric Architecture

The platform organizes functionality around 6 business module categories, not generic CRUD.

- Modules are grouped into: Planning (规划), Design (设计), Management (管理), Acceptance (验收), Review (复盘), Enablement (赋能)
- Each module MUST have differentiated form fields matching its business purpose — no two modules share identical schemas
- Rich text editors are required for document-oriented modules (PRD, risks, competitors, roadmap, meetings, acceptance, FAQ)
- Structured forms are required for data-oriented modules (requirements, parameters, test cases)
- Navigation MUST use a collapsible category sidebar, not flat tabs

**Rationale**: The current implementation's homogenized forms (title + priority + text) fail to capture the distinct business semantics of each PM activity. Differentiated schemas enable richer analysis, better AI assistance, and proper traceability.

### III. AI-Assisted, Human-Confirmed

All AI-generated outputs are suggestions. The human PM retains full authority.

- AI-generated PRD sections, test cases, risk assessments, and competitor analysis MUST be presented in draft state
- Destructive operations (delete, bulk update, cross-project actions) triggered by AI MUST require explicit confirmation
- AI-suggested traceability links between entities MUST be flagged as "pending confirmation" until approved
- The Agent MUST read current navigation context before making suggestions and MUST NOT assume state

**Rationale**: Product decisions carry business consequences. AI hallucinations in PRD scope or risk assessment can lead to costly misdirection. Human confirmation is a non-negotiable safety gate.

### IV. Data Isolation & Traceability

Project data is strictly isolated. Relationships between entities are explicitly tracked.

- Every database table MUST include `project_id` for automatic query scoping
- Cross-project data access is PROHIBITED at the API layer
- Entity relationships (requirement → parameter → test case → PRD section) MUST be stored in a dedicated relations table with confidence scores
- Bidirectional traceability MUST be supported: given any entity, the system can traverse both upstream (what depends on this) and downstream (what this depends on)
- File attachments MUST be stored under `data/projects/{projectId}/`

**Rationale**: PM work involves sensitive product strategy. Data isolation prevents accidental leakage between projects. Traceability ensures impact analysis when requirements change.

### V. Version-Controlled Documentation

All documents support snapshot, compare, and rollback.

- Every document entity MUST support version snapshots with explicit version numbers (e.g., v1.0, v1.1)
- Version comparison MUST show structural diffs, not just text diffs
- Rollback to any previous version MUST be supported
- Cross-version references MUST be tracked to detect stale links after updates
- Auto-save drafts MUST be stored separately from committed versions

**Rationale**: PRDs and requirements evolve through review cycles. Without version control, teams lose the ability to audit what changed, when, and why — critical for compliance and retrospectives.

## Additional Constraints

### Technology Stack

- **Frontend**: SvelteKit (matching Open WebUI's existing architecture)
- **Backend**: Open WebUI's existing API layer with PM-specific extensions
- **Database**: SQLite (local) / PostgreSQL (production) via Open WebUI's ORM
- **Rich Text**: Integrate with Open WebUI's existing editor or a compatible Markdown-rich component
- **AI Integration**: OpenAI/Claude/local models via user-configured API keys
- **Styling**: Must conform to Open WebUI's Tailwind CSS design system and theming

### Data Compatibility

- Existing data in `{text: string}` format MUST be migrated gracefully to new differentiated schemas
- New fields MUST have sensible defaults for backward compatibility
- API layer MUST support both old and new field structures during transition

### Performance

- Rich text editor MUST handle documents up to 50,000 words without degradation
- Table views with 1,000+ rows MUST support virtual scrolling
- Page load for module switching MUST complete within 500ms

## Development Workflow

### Phase-Driven Delivery

Implementation follows the 7-phase plan defined in the PRD:

1. **Phase 1**: Core framework + Project + Agent (foundation)
2. **Phase 2**: PRD editing + checks + parameter lists (document闭环)
3. **Phase 3**: Requirements + competitor analysis + prototypes (planning modules)
4. **Phase 4**: Versioning + traceability + workflows (core capabilities)
5. **Phase 5**: Management + acceptance modules (management闭环)
6. **Phase 6**: Retrospective + enablement modules (completion)
7. **Phase 7**: Testing + optimization + documentation (stabilization)

Each phase MUST deliver independently testable increments. No phase may assume a future phase's completion.

### Code Organization

- PM-specific components reside in `src/lib/components/pm/`
- PM API layer extends `src/lib/apis/pm/`
- Module-specific logic MUST be colocated: planning modules together, design modules together, etc.
- Shared UI primitives (rich text, tables, forms) MUST be reusable across modules

### Review Gates

- All UI changes MUST be verified against Open WebUI's existing design system
- API changes MUST maintain backward compatibility during transition
- AI-assisted features MUST include manual-fallback test cases
- Data migration scripts MUST be tested against a copy of production data

## Governance

This constitution supersedes all other development practices for the PM Workflow Platform scope.

### Amendment Procedure

1. Proposed amendments MUST be documented in `.orgii/plans/` with impact analysis
2. Amendments affecting Core Principles require explicit approval
3. Template files (plan, spec, tasks, checklist) MUST be updated when principles change
4. A 24-hour review period is REQUIRED before ratifying amendments

### Versioning Policy

- **MAJOR**: Removal or redefinition of a Core Principle; breaking changes to module architecture
- **MINOR**: Addition of new principles or sections; material expansion of existing guidance
- **PATCH**: Clarifications, wording improvements, non-semantic refinements

### Compliance Review

- Constitution compliance MUST be verified before each phase's planning phase
- The `/speckit-plan` command MUST reference the Constitution Check gate
- Deviations MUST be documented in the plan's Complexity Tracking section with justification

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): Confirm with team | **Last Amended**: 2026-06-28
