# AI Requirement Workflow - Idea → Brainstorm → PRD with multi-role review

## Goal

Build an AI-powered requirement design workflow: Idea → Brainstorm/Research → PRD, with multi-agent requirement review and PRD generation capabilities.

## Background

- Backend flow engine already supports `requirement_to_prd`, `requirement_to_parameter`, `full_chain`
- `BaseSkill` class exists with `system_prompt`, `build_user_message()`, `parse_response()`, `fallback_response()`
- `PRDGenerationSkill` and `RequirementAnalysisSkill` already exist
- Agent chat API (`/pm/agent/chat`) already dispatches to skills via `_call_llm`
- The workflow page (`/pm/[projectId]/workflow`) currently uses hardcoded mock data
- Issue references: `qili80193-collab/pm-req-clear` (WHY→WHAT→HOW framework) and `spec-first-master` project

## Requirements

### R1: AI Requirement Workflow (Idea → Brainstorm → PRD)
- Add a new flow template `idea_to_prd` that chains: Idea entry → AI Brainstorm/Research → Requirement Analysis → PRD Generation
- The workflow page should integrate with the flow engine to execute this pipeline
- Each step produces a PM entry with proper traceability (derives relations)

### R2: Multi-Agent Requirement Review
- Create a new `RequirementReviewSkill` that simulates multi-role review
- Roles: Product Manager, Tech Lead, UX Designer, QA Lead
- Each role generates review comments from their perspective
- Results are merged into a single review summary with categorized findings (critical/medium/low)
- Review can be triggered from the requirement module page or agent chat

### R3: PRD Generation with Template
- Enhance `PRDGenerationSkill` to support custom PRD templates
- Templates are SPEC entries with `role: 'template'` and `specCategory: 'prd-template'`
- If no custom template, use the built-in standard template (existing behavior)
- Generated PRD sections map to entries with derives relations back to source requirements

### R4: Workflow Page Integration
- Replace mock data in workflow page with flow-engine-backed steps
- Each workflow step shows: status (from entry existence), AI action buttons, linked deliverables
- "Start" button triggers the appropriate flow via `/pm/flow/execute`
- Progress tracked by checking which entries exist in each module

## Acceptance Criteria

- [ ] `idea_to_prd` flow template registered in `FLOW_TEMPLATES` with proper step chain
- [ ] `_flow_idea_to_prd` executor function implemented following existing patterns
- [ ] `RequirementReviewSkill` class with 4-role review system
- [ ] Multi-role review produces merged categorized summary
- [ ] PRD generation supports custom templates from SPEC entries
- [ ] Workflow page shows real data from flow engine instead of mock
- [ ] Workflow steps link to actual module deliverables
- [ ] All new code uses `_extract_json` for LLM response parsing (never `json.loads` directly)
- [ ] All new code uses DB-direct access pattern (never HTTP self-calls)

## Out of Scope

- Full brainstorm/research agent (separate complex feature)
- Workflow step auto-advancement based on entry status
- Custom workflow template creation UI
