# PM Features - Issue #18: Prototype Annotation, AI Req Workflow, Architecture Diagram

## Goal

Implement three major PM features from GitHub Issue #18: prototype annotation linking, AI-powered requirement workflow, and auto-synced product architecture diagram.

## Background

The PM module already has 16 module types, a flow engine with AI-powered content generation, annotation support (`PMAnnotationPanel`, `EntryAnnotation` type), a mindmap component (`PMMindMap`) for product-architecture, and agent skills (PRD generation, requirement analysis). The workflow page is currently mock-data only.

## Child Tasks

1. **pm-prototype-annotation** — Link prototype elements to requirements/SPEC/parameters with boundary markers
2. **pm-ai-req-workflow** — Idea → Brainstorm/Research → PRD workflow with multi-agent review and PRD generation
3. **pm-architecture-diagram** — Auto-sync product architecture diagram with module/feature versions

## Cross-Child Acceptance Criteria

- [ ] All three features integrate into the existing PM module navigation and routing
- [ ] Each feature follows the module registration checklist (types → config → groups → labels → icons → counts)
- [ ] AI features use the existing `_call_llm` + `BaseSkill` pattern
- [ ] New modules store structured data in `entry.data` consistent with existing patterns

## Out of Scope

- Feature #6 from Issue #18 (empty/unspecified — skipped)
- Migration of existing workflow page from mock data (separate task)
