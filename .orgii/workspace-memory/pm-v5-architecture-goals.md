---
name: PM v5 Architecture Goals
description: User's 6-point mandate for PM workspace deep integration and completion — highest execution approval granted
type: workspace
---

**Date:** 2026-07-02

The user issued a 6-point mandate to complete the PM workspace, granting **highest execution approval** for autonomous planning and implementation. This supersedes prior v2/v3/v4 scopes and represents the final integration phase.

**The 6 Goals:**

1. **Module & Base Info Alignment** — Every module must align with base information functionality. All modules should have consistent base info fields and behaviors.

2. **File Version ↔ Base Info Integration** — File versions must be connected with base information, with version comparison functionality persisted for reference.

3. **Project Version ↔ File Version Integration** — Project-level versions must be linked to file-level versions, creating a two-tier version hierarchy.

4. **Traceability ↔ Version Flow Integration** — Traceability must be associated with each version's lifecycle flow, with automatic reasonableness validation.

5. **Agent Integration** — Agent functionality should directly use OpenWebUI's Agent capabilities, OR build a dedicated tool module that interfaces with these features. A generic module should be created to enable rapid workflow development.

6. **Completion** — All current features are prototypes; they need to be completed and integrated end-to-end.

**Why:** The PM workspace has many incomplete features (traceability, versioning, base modules). The user wants everything connected and functional, not just individual features working in isolation. They explicitly rejected the current state as "just a prototype" and want production-ready integration.

**How to apply:** This is the highest-priority work. When planning implementation, prioritize: (1) data model alignment across modules, (2) version hierarchy (project → file), (3) traceability with version-aware validation, (4) Agent integration as a reusable generic module. The user has granted full autonomy — make architectural decisions and implement them directly.

**Implementation Plan (5 phases):**

- **Phase 1 (1-2d):** Module base info alignment — unify field definitions in `types.ts`, complete `moduleConfig` for all modules, add base info panel to module page.
- **Phase 2 (2-3d):** Version integration — link project versions to entry versions, implement version comparison API, add version snapshot UI.
- **Phase 3 (2-3d):** Traceability + version flow — add `version_snapshot` to relations, implement reasonableness validation rules, add version timeline to traceability graph.
- **Phase 4 (3-4d):** Agent generic module — build `PMAgentTool.svelte`, implement Skill routing in `agentChatStore`, create PRD generation / requirement analysis / parameter extraction / testcase generation / version compare / relation suggest Skills.
- **Phase 5 (2-3d):** Completion — wire workflow page to real data, implement Excel import/export, PRD checks, prototype review, end-to-end testing.

**OpenWebUI Integration Targets (from docs review, 2026-07-02):**

The user explicitly asked to review OpenWebUI docs for features to incorporate. The following are confirmed integration targets, prioritized by PM value:

| OpenWebUI Feature | PM Application | Priority |
|-------------------|---------------|----------|
| **Tools (Code Interpreter)** | Data analysis reports, risk matrix visualization, Gantt chart generation | P0 |
| **Knowledge / RAG** | Semantic search across PRD/requirement docs, auto parameter extraction from PRD | P0 |
| **Model Presets** | Dedicated agents: PRD Generator, Requirement Analyst, Testcase Generator | P0 |
| **Task Management** | Multi-step Skill workflows (PRD → Parameters → Testcases) | P1 |
| **Memory** | Persist project context and user preferences across sessions | P1 |
| **Web Search** | Competitor analysis auto-research | P1 |
| **Notes (AI Enhance)** | In-place AI rewrite/optimization of PRD sections | P2 |
| **Channels (@model)** | Multi-model collaborative review (e.g., `@claude` critiques PRD, `@gpt-4o` generates tests) | P2 |
| **Open Terminal** | Agent executes code to generate reports/charts | P2 |

**Key architectural decisions from docs review:**
- Reuse OpenWebUI's existing `generateOpenAIChatCompletion` and `modelsStore` for model access — do NOT build parallel model infrastructure.
- Agent Skills should be implemented as OpenWebUI **Model Presets** (system prompt + bound tools + knowledge) where possible, falling back to custom Skill classes only when PM-specific logic is needed.
- Knowledge bases for PM projects should leverage OpenWebUI's vector DB (ChromaDB/PGVector) rather than building a separate RAG system.
- The generic Agent module (`PMAgentTool.svelte`) should expose an interface compatible with OpenWebUI's tool/function calling conventions so future Skills can be added without code changes.

**Current System State (from code review, 2026-07-02):**

The PM workspace is built on top of OpenWebUI (SvelteKit + Python FastAPI). Current architecture:

- **Frontend:** SvelteKit with Svelte 5, TipTap for rich text, Tailwind CSS
- **Backend:** Python FastAPI with SQLAlchemy async ORM, SQLite/PostgreSQL
- **Data model:** Single `PMEntry` table with `module_type` discriminator (prd, requirement, parameter, etc.)
- **API layer:** `backend/open_webui/routers/pm.py` with project/entry/version endpoints
- **Agent:** Custom PM agent with intent detection + skill classes, NOT using OpenWebUI's native agent system

**Gap Analysis — what exists vs what's needed (PRD-aligned):**

| Feature | Current State | PRD Target | Needed For v5 |
|---------|--------------|-----------|---------------|
| Module base info | `PMEntry` has title/content/data/status/priority/version — basic but consistent | 14 modules with dedicated tables/schemas per PRD | Add `moduleConfig` per type, base info panel, field validation |
| File versioning | Entry-level versions (PMEntryVersion table + APIs) exist but UI is placeholder | Full version control: snapshots, compare, rollback, branch/merge | Link to project versions, version comparison, persisted diff |
| Project versioning | PMVersion table exists, version card on dashboard | Project versions tied to deliverables, two-tier hierarchy | Two-tier hierarchy, project version → entry version mapping |
| Traceability | PMRelation table + traceability page with xyflow graph | Bidirectional trace + impact analysis with version-aware validation | Version-aware relations, reasonableness validation, timeline |
| Agent | Custom skill classes in pm.py | Generic agent module using OpenWebUI native agent/tools | Generic agent module, OpenWebUI integration, tool calling |
| Module completeness | 14 modules defined, some are stubs (prototype, schedule, acceptance) | All 14 modules fully functional with proper editors | All modules functional with proper editors |
| Workflow | Basic workflow steps | Full workflow engine with AI-extracted data, manual override | Workflow engine with step management |
| PRD editing | Rich text editor with basic sections | Full PRD editor with section management, parameter embedding, AI generation | Section sidebar, parameter embed, AI generation |
| Requirements | Basic table view | Full requirement collection with Excel import/export, AI analysis | Excel I/O, AI analysis |
| Competitor analysis | Basic table | Full competitor matrix with AI research | Competitor matrix, AI research |
| Roadmap | Basic gantt with time scale | Full roadmap with dependencies, milestones, calendar sync | Dependencies, milestones, calendar sync |
| Parameters | Basic parameter table | Full parameter list with extraction from PRD, config generation | PRD extraction, config generation |
| Testcases | Basic testcase table | Full testcase management with AI generation, execution tracking | AI generation, execution tracking |
| Schedule | Basic schedule form | Full schedule with甘特图, dependencies, calendar sync |甘特图, dependencies, calendar sync |
| Risk | Basic risk table | Full risk matrix with probability/impact scoring | Risk matrix visualization |
| Deliverables | Not implemented | Full deliverable checklist with status tracking | Deliverable tracking |
| Acceptance | Not implemented | Full acceptance documentation with criteria | Acceptance workflow |
| Issues | Basic issue table | Full issue tracking with requirement linkage | Requirement linkage |
| Retrospective | Not implemented | Full retrospective with lessons learned | Retrospective workflow |
| Training/Manual/FAQ/Presentation | Not implemented | Full enablement materials | Enablement modules |

**Backend Tables (from `backend/open_webui/models/pm.py`):**
- `PMProject` — project root
- `PMVersion` — project-level versions
- `PMEntry` — module entries (unified table with module_type discriminator)
- `PMEntryVersion` — entry-level version snapshots
- `PMEntryBranch` — branches per entry
- `PMEntryMerge` — merge records with conflicts
- *(Note: PMRelation table not yet created — planned for traceability)*

**PRD-Defined Tables (not yet implemented):**
The PRD defines many more tables than currently exist:
- `workflows` — workflow engine with steps
- `entities` / `relations` — traceability graph (exists partially)
- `requirements` — dedicated requirement table (currently in PMEntry.data)
- `competitors` / `competitor_analysis` — competitor matrix
- `roadmap_nodes` — roadmap with dependencies
- `prd_documents` — dedicated PRD table with sections
- `prd_checks` / `check_rules` — PRD validation
- `prototype_screens` / `prototype_checks` — prototype review
- `parameters` — dedicated parameter table
- `prototype_prompts` — AI prompt generation
- `testcases` — dedicated testcase table
- `project_init` — project charter
- `schedule_tasks` — schedule with甘特图
- `meeting_notes` — meeting minutes
- `risks` — risk matrix
- `deliverables` — deliverable checklist
- `acceptance` / `acceptance_items` — acceptance criteria
- `issues` — issue tracking
- `data_reports` — data analysis
- `retrospectives` — version retrospective
- `iterations` — iteration plans
- `training_materials` / `manuals` / `faqs` / `presentations` — enablement

**Frontend Module List (from `src/routes/(app)/pm/[projectId]/+page.svelte`):**
Planning: prd, requirement, roadmap
Design: parameter, product-architecture, prototype, competitor
Execution: schedule, testcase, risk, meeting
Review: acceptance, faq

**Original Design Documents (Authoritative Source):**
The complete PM Workflow Platform design is documented in `docs/prd/` (reviewed 2026-07-02):
- `PM-Workflow-Platform-PRD-v1.0.md` — Full product requirements: 28 actions across 14 modules (planning, design, execution, review, enablement)
- `PM-Workflow-Platform-DB-Design-v1.0.md` — Drizzle ORM schema: projects, versions, workflows, entities, relations, requirements, competitors, roadmap, prd_documents, parameters, testcases, schedules, risks, deliverables, acceptance, issues, retrospectives, iterations, training, manuals, faqs, presentations
- `PM-Workflow-Platform-API-Design-v1.0.md` — Agent Native action definitions for all modules
- `PM-Workflow-Platform-Implementation-Plan-v1.0.md` — 7-phase, 12-week plan with milestones

These PRD documents represent the *target state* for the PM workspace. Current implementation is a partial prototype. The v5 mandate is to bridge the gap between current state and PRD design.

**Key Files:**
- `src/lib/apis/pm/types.ts` — shared types (ModuleEntry, Version, Relation, etc.)
- `src/lib/apis/pm/index.ts` — HTTP client (getOne/create/update/remove)
- `src/lib/apis/pm/version.ts` — version API calls (frontend already has full API)
- `backend/open_webui/routers/pm.py` — backend router (needs relation endpoints)
- `backend/open_webui/models/pm.py` — database models (needs PMRelation table)
- `src/routes/(app)/pm/[projectId]/[module]/+page.svelte` — module page (dynamic routing)
