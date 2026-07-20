# Feature Specification: PM Skills Integration

**Feature Branch**: `[003-pm-skills-integration]`

**Created**: 2026-07-11

**Status**: Draft

**Input**: User description: "根据 constitution 进行规划设计：https://github.com/phuryn/pm-skills；https://docs.timbal.ai/（https://github.com/timbal-ai/timbal）"

**关联准则**: `.specify/memory/constitution.md` v1.2.1 | `specs/002-agent-data-platform/design-principles.md`

---

## Clarifications

### Session 2026-07-11

- **Q1**: pm-skills 技能映射方式 → **A**: 参考现有产品的 skill 导入方式，并在工作流中绑定对应的 skill。管理员通过工作流配置界面将 pm-skills 命令绑定到 SkillContract，每个绑定需经过审核确认。
- **Q2**: pm-skills 技能内容存储位置 → **A**: 全量本地存储。所有 pm-skills SKILL.md 文件复制到项目仓库的 `backend/open_webui/pm/skills/pm-skills/` 目录下，作为项目的一部分进行版本管理。
- **Q3**: pm-skills 版本更新策略 → **D**: 固定版本不更新。项目锁定初始版本的 pm-skills 内容，后续如需更新由管理员手动操作。Open WebUI 已有 skill 导入模块，pm-skills 作为外部 skill 模块导入后固定引用，工作流直接调用引用的 skill 即可。
- **Q4**: 工作流调用 pm-skills 的方式 → **B**: 通过 Skill ID 引用。工作流配置中指定引用的 skill ID（如 `pm-skills/prd-generation`），运行时通过统一注册表解析并调用对应的 SkillContract。
- **Q5**: 链式技能调用的上下文传递方式 → **B**: 显式输出绑定。工作流配置中明确指定前一个 skill 的哪个输出字段映射到后一个 skill 的哪个输入字段，确保数据流清晰可追踪。

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 用户通过 Agent 调用 pm-skills 方法论生成结构化产物 (Priority: P1)

As a product manager, I want the Agent to invoke pm-skills methodologies (e.g., `/discover`, `/write-prd`, `/strategy`) and produce structured outputs that conform to our SkillContract, so that I get rigor of proven PM frameworks with outputs that automatically land in our ModuleEntry system.

**Why this priority**: This is the core value proposition — bringing 68+ PM skills into the Open WebUI PM workspace as reusable, contract-validated capabilities. Without this, the Agent cannot leverage external PM expertise.

**Independent Test**: Trigger `/discover` on a new product idea. Verify the Agent loads the `brainstorm-ideas`, `identify-assumptions`, `prioritize-assumptions`, and `brainstorm-experiments` skills from pm-skills, produces structured output per SkillContract, and presents it as a draft requiring confirmation before persisting to ModuleEntry.

**Acceptance Scenarios**:

1. **Given** a user invokes `/discover` with a product idea, **When** the Agent processes the request, **Then** it loads the relevant pm-skills methodology skills, injects them into the prompt, and produces output validated against the skill's `outputContract`.
2. **Given** the output is produced, **When** presented to the user, **Then** it is shown as a suggestion requiring explicit confirmation (per Constitution Principle III), and only persists after approval.
3. **Given** a pm-skills command requires multiple chained skills (e.g., `/discover` = 4 skills), **When** executed, **Then** each skill's output feeds into the next as context, with the final result being a unified structured output.

---

### User Story 2 - 用户显式调用 pm-skills 命令获得确定性输出 (Priority: P1)

As a product manager, I want to type `/pm-discover` or `/pm-write-prd` to invoke a specific pm-skills command deterministically, so that I get predictable, framework-driven results without the Agent guessing which skill to use.

**Why this priority**: Explicit invocation is the foundation of trust. Users must be able to trigger specific PM frameworks on demand, matching the pm-skills command experience (`/discover`, `/write-prd`, etc.).

**Independent Test**: Type `/pm-write-prd Smart notification system that reduces alert fatigue` in the agent chat. Verify the Agent loads the `create-prd` skill, follows the 8-section PRD template, and returns a structured draft.

**Acceptance Scenarios**:

1. **Given** a user types `/pm-write-prd` with a feature description, **When** the command is submitted, **Then** the system resolves the `create-prd` skill from the registry and invokes it explicitly.
2. **Given** the skill produces a PRD draft, **When** generation completes, **Then** the output is validated against the skill's `outputContract` (JSON Schema) before any persistence.
3. **Given** the validated output, **When** presented to the user, **Then** it follows the pm-skills PRD template structure (8 sections) and requires explicit confirmation before persistence.

---

### User Story 3 - Agent 按需加载 pm-skills 方法论作为上下文增强 (Priority: P2)

As a product manager chatting with the Agent, I want the Agent to automatically load relevant pm-skills methodologies based on conversation context (e.g., discussing pricing loads `pricing-strategy` skill), so that I get framework-guided answers without explicitly invoking commands.

**Why this priority**: This enables "invisible" PM expertise — the Agent naturally draws on proven frameworks without user intervention, enhancing every interaction.

**Independent Test**: Ask the Agent "How should we price our new AI feature?" without any command. Verify the Agent loads the `pricing-strategy` skill from pm-skills, references its methodology, and structures the answer accordingly.

**Acceptance Scenarios**:

1. **Given** a natural-language request about pricing, **When** the Agent processes it, **Then** it detects the topic relevance and loads the `pricing-strategy` skill methodology into context.
2. **Given** the loaded skill has an `outputContract`, **When** the Agent answers, **Then** the response structure conforms to the skill's output schema (e.g., pricing models, competitive analysis, willingness-to-pay).
3. **Given** no pm-skills skill matches the request topic, **When** the Agent responds, **Then** it answers in general mode without fabricating skill usage.

---

### User Story 4 - 管理员配置 pm-skills 与 SkillContract 的映射关系 (Priority: P2)

As a platform administrator, I want to configure which pm-skills commands map to which SkillContracts and define their output schemas, so that the integration is maintainable and extensible.

**Why this priority**: Mapping configuration is essential for maintainability — when pm-skills updates or new skills are added, administrators need a declarative way to register them without code changes.

**Independent Test**: Add a new pm-skills command `/pm-market-scan` mapping to the `market-scan` skill. Verify it appears in the skill registry and can be invoked immediately.

**Acceptance Scenarios**:

1. **Given** an administrator defines a new pm-skills → SkillContract mapping, **When** saved, **Then** the skill appears in the unified registry with correct `id`, `description`, `outputContract`, and `invocation` settings.
2. **Given** a mapped skill has an `outputContract`, **When** invoked, **Then** the output is validated against that schema before persistence.
3. **Given** a pm-skills skill has no corresponding `outputContract` defined, **When** invoked, **Then** it operates as a methodology-only skill (knowledge injection, no structured output validation).

---

### Edge Cases

- What happens when a pm-skills command chains multiple skills but one skill's output violates the next skill's `inputSchema`? (Resolution: return error to user with details; allow retry or manual edit; do not silently proceed.)
- What happens if the pm-skills repository updates and a skill's methodology changes? (Resolution: methodology is versioned; new versions require manual re-mapping review by admin.)
- What happens if a pm-skills skill's methodology conflicts with the user's instruction? (Resolution: User instruction wins; methodology is guidance, not a hard constraint — per Constitution Principle III.)
- What happens if Timbal workflow fails mid-run during skill invocation? (Fall back to raw data + notice; never return half-processed data silently.)

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a unified skill registry that holds both native PM skills and pm-skills methodology skills, each as a `SkillContract`.
- **FR-002**: Every pm-skills command MUST be mappable to a `SkillContract` with: `id` (kebab-case), `name`, `description`, `outputContract`, `invocation` (explicit/autonomous/both), and `requiresConfirm` (MUST be true for writes).
- **FR-003**: The system MUST support explicit invocation via `/pm-<id>` command for pm-skills commands, resolved deterministically from the registry.
- **FR-004**: The system MUST support autonomous skill loading — the Agent detects conversation context and loads relevant pm-skills methodologies automatically.
- **FR-005**: All pm-skills write operations MUST pass through the existing confirmation gate (`requiresConfirm=True`, Constitution Principle III).
- **FR-006**: pm-skills skills with `methodologyRef` MUST inject the SKILL.md content into the Agent prompt as guidance.
- **FR-007**: pm-skills skills with `outputContract` MUST validate output against that JSON Schema before persistence to `ModuleEntry`.
- **FR-008**: Chained pm-skills commands (e.g., `/discover` = 4 skills) MUST pass output from one skill as context to the next, with the final result being a unified structured output.
- **FR-009**: The system MUST support mapping configuration — administrators can declaratively add/remove pm-skills → SkillContract mappings without code changes.
- **FR-010**: pm-skills skills without an `outputContract` MUST operate as methodology-only skills (knowledge injection, no structured output validation).
- **FR-011**: All pm-skills operations MUST remain scoped by `project_id`; cross-project access is PROHIBITED (Constitution Principle IV).
- **FR-012**: The system MUST support version pinning — when pm-skills updates, existing mappings continue to work with the pinned version until explicitly updated.

### Key Entities *(include if feature involves data)*

- **PmSkillsMapping**: Configuration mapping pm-skills commands to SkillContracts. Key attributes: commandId, skillContractId, version, methodologyRef, outputContractId, enabled.
- **PmSkillsVersion**: Version tracking for pm-skills integration. Key attributes: commandId, version, methodologyHash, updatedAt.
- **SkillContract**: Registry metadata for a generic skill module (existing). Key attributes: id, name, description, category, inputSchema, outputContract, methodRef, methodologyRef, invocation, requiresConfirm.
- **ModuleEntry**: Existing unified data model (existing). Key attributes: id, projectId, moduleType, title, content, data, metadata, version.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can invoke any mapped pm-skills command via `/pm-<id>` and receive a contract-validated draft within the agent's response time (Tool call ≤ 3s per Constitution Performance).
- **SC-002**: 100% of pm-skills write operations require explicit user confirmation before persisting to ModuleEntry.
- **SC-003**: In autonomous mode, the Agent correctly loads relevant pm-skills methodologies for ≥80% of PM-related queries (measured via conversation analysis).
- **SC-004**: Chained pm-skills commands (e.g., `/discover`) produce unified output that validates against the final skill's `outputContract`.
- **SC-005**: 0 cross-project data leaks at the API layer (Constitution Principle IV enforced).
- **SC-006**: Administrators can add a new pm-skills → SkillContract mapping without code changes, and it becomes available for invocation within 1 minute.

## Assumptions

- The pm-skills repository (https://github.com/phuryn/pm-skills) provides 68+ PM skills as SKILL.md files with standardized metadata.
- pm-skills commands follow a consistent pattern: `/command-name` triggers a chain of one or more skills.
- The project already has `SkillContract` and `ModuleEntry` as unified data models (Constitution Principle VI, existing `data-model.md`).
- Timbal is embeddable as a Python library within the backend `pm/` module for deterministic workflows only (Constitution Principle VI).
- Open WebUI native Agent/Tools/Skills/Pipeline/Knowledge APIs are the orchestration layer (Constitution Principle VI, not replaced by Timbal or pm-skills).
- The frontend is SvelteKit + Tailwind, consistent with existing Open WebUI architecture.
- AI services may be unavailable; skills MUST degrade to manual-only or general-mode gracefully (Constitution Principle I).
