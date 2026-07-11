# Feature Specification: Agent 与数据平台（Skill 通用模块 + 数据流水线）

**Feature Branch**: `[002-agent-data-platform]`

**Created**: 2026-07-11

**Status**: Draft

**Input**: User description: "基于 open-pm-webui 沉淀 PM 工作数据并打通联系，作为规范化模块供 Agent 沉淀/提取/思考/使用。下一步打通 webui 的 agent，让用户无感后台流程，规范产品数据。需要：Agent 集成方案、数据流水线、产品数据规范化架构、分阶段路线图。skill 应为通用模块，调用时用户可指定或 Agent 自主选择。先出设计准则约束后续 AI 开发，再分阶段实施。"

**关联准则**: `design-principles.md` ｜ **路线图**: `roadmap.md` ｜ **架构**: `architecture.md` ｜ **数据模型**: `data-model.md`

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 用户通过命令显式调用通用技能 (Priority: P1)

As a product manager, I want to type `/pm-<skill>` (or pick from a skill palette) to invoke a specific capability, so that I get a structured result that I can confirm and persist without the agent guessing.

**Why this priority**: This is the most basic, predictable interaction. Without explicit invocation, users cannot trust or control which capability runs. It is the foundation of the "通用模块 + 双调用" principle.

**Independent Test**: Type `/pm-prd-generation` in the agent chat while a project is open. Verify the skill runs deterministically, returns a structured draft, and requires confirmation before persisting to ModuleEntry.

**Acceptance Scenarios**:

1. **Given** a project is open and the user types `/pm-prd-generation`, **When** the command is submitted, **Then** the system resolves the skill from the registry by `id` and invokes it explicitly (not via autonomous selection).
2. **Given** a skill produces a document draft, **When** generation completes, **Then** the output is validated against the skill's `outputContract` (JSON Schema) before any persistence.
3. **Given** the validated output, **When** presented to the user, **Then** it is shown as a suggestion requiring explicit confirmation (per Constitution Principle III), and only persists after approval.

---

### User Story 2 - Agent 依据上下文自主选择并调用技能 (Priority: P1)

As a product manager chatting with the agent, I want the agent to autonomously pick the most relevant skill for my request, so that I don't have to memorize command names.

**Why this priority**: "让用户无感后台流程" requires the agent to self-select capabilities. But autonomy must stay transparent and within scope.

**Independent Test**: Ask the agent "帮我分析这个项目的风险" without any command. Verify the agent selects a risk-analysis skill from the registry, states which skill it chose and why, then runs it.

**Acceptance Scenarios**:

1. **Given** a natural-language request and the skill registry summary injected by Pipeline, **When** the agent responds, **Then** it selects one or more matching skills and **MUST** echo the chosen `skill id` plus a one-line reason.
2. **Given** the agent selected an autonomous-enabled skill, **When** it runs, **Then** the flow follows the same `outputContract` validation and confirmation gate as explicit invocation.
3. **Given** no skill matches the request, **When** the agent cannot find a fit, **Then** it responds in general mode without fabricating a skill or bypassing the registry.

---

### User Story 3 - Agent 调用时按需标准化项目数据 (Priority: P1)

As a product manager, I want the agent to always reason over clean, standardized project data, so that its answers are consistent and traceable.

**Why this priority**: Data quality is the prerequisite for every downstream Agent capability. On-demand (not real-time, not batched) balances freshness and cost per our root decision #3.

**Independent Test**: Trigger any agent request on a project with messy entries. Verify a Timbal workflow runs once (采集→清洗→标准化), producing NormalizedEntry, and the agent's answer cites normalized data.

**Acceptance Scenarios**:

1. **Given** an agent request on `project_id=X`, **When** the Pipeline injects the project context, **Then** the Timbal workflow is awakened once to collect/clean/standardize `ModuleEntry` of project X.
2. **Given** the standardization runs, **When** it completes, **Then** the result is idempotent (re-running yields the same NormalizedEntry) and failures fall back to raw data with a notice.
3. **Given** normalized data, **When** the agent answers, **Then** structured data is fetched via `pm_*` Tools and document data via Knowledge RAG (dual-track).

---

### User Story 4 - 文档类数据可语义检索且带来源引用 (Priority: P2)

As a product manager, I want the agent to retrieve PRD/meeting/competitor docs semantically and cite sources, so that answers are grounded.

**Why this priority**: Dual-track supply (root decision #4) requires the RAG leg to be trustworthy with citations (Constitution Principle VI RAG).

**Independent Test**: Ask the agent a question answerable only from a PRD in the project's Knowledge base. Verify the answer cites the source `/pm/{projectId}/prd/{entryId}`.

**Acceptance Scenarios**:

1. **Given** project documents are chunked into Knowledge, **When** the agent retrieves them, **Then** each cited chunk includes its `source` reference back to ModuleEntry.
2. **Given** a retrieved chunk, **When** the agent answers, **Then** it surfaces the source link to the user.

---

### User Story 5 - pm-skills 方法论约束高价值技能产出 (Priority: P2)

As a product manager, I want PM methodologies (e.g., opportunity solution tree) to guide the agent and force structured output, so that outputs follow best practice and stay normalized.

**Why this priority**: This realizes root decision #2 — methodology drives "how to think", outputContract drives "must land in ModuleEntry".

**Independent Test**: Invoke a Top-10 skill linked to a SKILL.md. Verify the agent follows the methodology and the result conforms to the skill's outputContract.

**Acceptance Scenarios**:

1. **Given** a skill with `methodologyRef` to a SKILL.md, **When** invoked, **Then** the methodology is injected into the prompt as guidance.
2. **Given** the skill has an `outputContract`, **When** the result is produced, **Then** it is validated against that schema before persistence.

---

### Edge Cases

- What happens when two skills both match a request in autonomous mode? (Resolution: agent ranks by description similarity; ties → ask user or pick highest-priority category.)
- What happens if Timbal workflow fails mid-run? (Fall back to raw ModuleEntry + notice; never return half-standardized data silently.)
- What happens if a skill's `outputContract` rejects the LLM output? (Return error to user; allow retry or manual edit; do not persist.)
- What happens if `project_id` is missing (chat not bound to a project)? (Agent operates in general mode; skills requiring project context are disabled.)
- What happens if a SKILL.md methodology conflicts with the user's instruction? (User instruction wins; methodology is guidance, not a hard constraint.)

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a unified skill registry that holds both executable skills (Python classes) and methodology skills (SKILL.md references), each as a `SkillContract`.
- **FR-002**: Every skill MUST declare `id`, `name`, `description`, `outputContract`, and `invocation` (explicit/autonomous/both) per `architecture.md` §4.1.
- **FR-003**: The system MUST support explicit invocation via `/pm-<id>` command, resolved deterministically from the registry.
- **FR-004**: The system MUST support autonomous skill selection by the agent, and the agent MUST echo the chosen skill `id` and reason in its response.
- **FR-005**: All skill write operations MUST pass through the existing confirmation gate (`requires_confirm=True`, Constitution Principle III).
- **FR-006**: On each agent request, a Timbal workflow MUST run once (collect → clean → standardize) over the current `project_id`'s `ModuleEntry`, producing `NormalizedEntry`.
- **FR-007**: The standardization workflow MUST be idempotent and MUST fall back to raw data with a notice on failure.
- **FR-008**: Structured data MUST be supplied to the agent via `pm_*` Tools; document data MUST be supplied via Knowledge RAG (dual-track).
- **FR-009**: Knowledge chunks MUST carry a `source` reference back to the originating ModuleEntry, and agent answers MUST surface citations.
- **FR-010**: Skills with `methodologyRef` MUST inject the SKILL.md methodology into the prompt; skills with `outputContract` MUST validate output before persistence.
- **FR-011**: All operations MUST remain scoped by `project_id`; cross-project access is PROHIBITED (Constitution Principle IV).
- **FR-012**: The Pipeline MUST auto-inject `project_id`, `tool_ids`, `knowledge_ids`, and `skill_registry_summary` into every agent request.

### Key Entities *(include if feature involves data)*

- **SkillContract**: Registry metadata for a generic skill module. Key attributes: id, name, description, category, inputSchema, outputContract, methodRef, methodologyRef, invocation, requiresConfirm. (See `architecture.md` §4.1)
- **NormalizedEntry**: Standardized view of a ModuleEntry after the Timbal workflow. Key attributes: entryId, projectId, moduleType, standardizedFields, version, normalizedAt.
- **SkillInvocation**: A record of one skill execution. Key attributes: id, projectId, skillId, mode (explicit/autonomous), chosenReason, outputRef, confirmedBy, createdAt.
- **KnowledgeChunk**: A document chunk for RAG. Key attributes: entryId, projectId, moduleType, title, content, version, source. (See `architecture.md` §4.3)
- **ModuleEntry**: Existing unified data model (requirement/parameter/spec/etc.), scoped by `project_id`, with version and relations. (See `data-model.md`)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can invoke any registered skill via `/pm-<id>` and receive a contract-validated draft within the agent's response time (Tool call ≤ 3s per Constitution Performance).
- **SC-002**: In autonomous mode, 100% of skill invocations echo the chosen skill id and reason.
- **SC-003**: On-demand standardization completes for a typical project (≤ 200 entries) within 5s and is idempotent across repeated runs.
- **SC-004**: 100% of RAG-sourced agent answers include at least one `source` citation to ModuleEntry.
- **SC-005**: 0 cross-project data leaks at the API layer (Constitution Principle IV enforced).
- **SC-006**: All new Agent capabilities shipped in this program are either a `SkillContract` or a `pm_*` Tool — no scattered logic (anti-扩散 compliance).

## Assumptions

- The project already has `ModuleEntry` as the unified data model, scoped by `project_id` (Constitution Principle IV, existing `data-model.md`).
- Open WebUI native Agent/Tools/Skills/Pipeline/Knowledge APIs are the orchestration layer (Constitution Principle VI, not replaced by Timbal).
- Timbal is embeddable as a Python library within the backend `pm/` module for deterministic workflows only.
- pm-skills provides 68 SKILL.md files licensable for methodology ingestion; only Top-10 high-value ones get output contracts in this program.
- The frontend is SvelteKit + Tailwind, consistent with existing Open WebUI architecture.
- AI services may be unavailable; skills MUST degrade to manual-only or general-mode gracefully (Constitution Principle I).
