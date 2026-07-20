# Feature Specification: Agent Workflow Designer & Architecture Fix

**Feature Branch**: `[007-agent-workflow-designer]`

**Created**: 2026-07-11

**Status**: Draft

**Input**: User description: "Agent模块还不全面，workflow 我需要能看到数据流程转的编程，类似于dify那种，可以手动调整其中的流程。以及Agent 功能：https://github.com/nyepppp/open-pm-webui/issues/26，并携带修复产品架构图的功能。"

## Clarifications

### Session 2026-07-11

- **Q**: 工作流节点类型定义 → **A**: 混合模式（预置常用类型 + 自定义扩展）
  - **影响**: 预置节点类型包括：开始、结束、Agent调用、数据处理、条件分支、循环、并行聚合。自定义扩展节点允许用户通过脚本定义新节点行为，需注册到统一技能注册表。
  - **已更新**: Key Entities 章节（WorkflowNode 类型枚举）、Functional Requirements（FR-003 扩展为支持预置和自定义节点类型配置）
- **Q**: 工作流执行模式 → **A**: 服务端执行
  - **影响**: 所有工作流节点在服务端执行引擎中运行，客户端仅负责展示工作流设计器和执行状态。执行引擎需支持异步执行、状态持久化和错误恢复。服务端执行确保数据安全性和复杂计算能力。
  - **已更新**: User Story 1（Acceptance Scenario 4 明确服务端执行）、Assumptions（新增工作流执行环境假设）
- **Q**: 架构图修复范围 → **A**: 仅修复
  - **影响**: 修复工作聚焦在解决现有架构图的渲染错误和交互失效问题，不增加新功能。工作流数据流可视化通过独立的工作流设计器实现，架构图保持其原有的模块关系展示职责。
  - **已更新**: User Story 5（明确修复范围）、Assumptions（新增架构图修复范围假设）
- **Q**: Agent写入确认策略 → **A**: 本次会话全部允许按钮，危险操作需要确认（删除，覆盖）
  - **影响**: 当前会话中的Agent写入操作默认全部允许（用户可通过按钮控制），但危险操作（删除、覆盖）始终需要确认。未来版本可扩展为可配置策略。
  - **已更新**: Functional Requirements（FR-006 明确确认策略）、Edge Cases（新增用户拒绝确认的处理）
- **Q**: 工作流持久化范围 → **A**: 定义+完整历史
  - **影响**: 工作流保存时持久化定义（节点、边、配置）和完整执行历史（每次执行的输入、输出、状态、日志）。支持审计和回溯，但存储开销需考虑（建议设置历史保留策略）。
  - **已更新**: Key Entities（Workflow 新增 execution_history[]）、Success Criteria（SC-010 扩展为支持历史回溯）

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visual Workflow Designer (Priority: P1)

As a PM, I need a visual workflow designer similar to Dify that allows me to see and manually adjust data flow between nodes. I can drag nodes, connect them, and define how data transforms as it flows from one step to another.

**Why this priority**: This is the core feature request — enabling users to visually design and adjust agent workflows with full control over data transformation between steps.

**Independent Test**: Can be fully tested by creating a workflow with at least 3 connected nodes, verifying data flows correctly between them, and adjusting the flow manually.

**Acceptance Scenarios**:

1. **Given** a PM workspace exists, **When** the user opens the workflow designer, **Then** they see a canvas with draggable nodes representing workflow steps
2. **Given** nodes are placed on the canvas, **When** the user connects two nodes, **Then** a data flow edge is created showing how data moves between steps
3. **Given** a connected workflow, **When** the user clicks on a node, **Then** they can configure data transformation rules for that step
4. **Given** a configured workflow, **When** the user saves and runs it, **Then** data flows through the pipeline according to the defined connections and transformations

---

### User Story 2 - PM Workspace Session Persistence (Priority: P1)

As a PM, when I select a workspace in a chat session, the agent should be able to read all content from that workspace as if accessing a folder, enabling contextual conversations about project data.

**Why this priority**: Directly from Issue #26 — enables the agent to understand project context by reading workspace data, making conversations more productive.

**Independent Test**: Can be fully tested by binding a session to a PM workspace and asking the agent to summarize or reference specific documents from that workspace.

**Acceptance Scenarios**:

1. **Given** a chat session is active, **When** the user selects a PM workspace from a dropdown, **Then** the session is bound to that workspace
2. **Given** a session is workspace-bound, **When** the user asks about project requirements, **Then** the agent can reference and cite specific documents from the workspace
3. **Given** multiple PM workspaces exist, **When** the user switches workspaces mid-session, **Then** the agent updates its context to the new workspace
4. **Given** a workspace-bound session, **When** the user asks the agent to create a PRD, **Then** the agent can read existing documents for context before generating

---

### User Story 3 - Agent Capability: Workspace Data Access (Priority: P2)

As a PM, I want the agent to be able to actively plan and read data from any PM workspace module, then import relevant information into target modules.

**Why this priority**: From Issue #26 — extends agent capabilities beyond simple chat to active workspace management, enabling automated workflows like "read requirements and generate test cases."

**Independent Test**: Can be fully tested by instructing the agent to read requirements from one module and generate corresponding test cases in another module.

**Acceptance Scenarios**:

1. **Given** a workspace with requirements and test case modules, **When** the user asks the agent to "generate test cases from requirements", **Then** the agent reads requirements and creates test cases in the test case module
2. **Given** a workspace with PRD and parameter modules, **When** the user asks the agent to "extract parameters from PRD", **Then** the agent reads the PRD and populates the parameter module
3. **Given** a multi-module workspace, **When** the user asks the agent to "summarize project status", **Then** the agent reads all modules and provides a comprehensive summary
4. **Given** the agent is performing a cross-module operation, **When** a write operation is required, **Then** the system prompts for human confirmation before persisting changes

---

### User Story 4 - PM Module Integration: Documents/Skills (Priority: P2)

As a PM, I want fixed workflows that can transform requirement documents into structured outputs, trace data lineage, and support ideation/brainstorming workflows.

**Why this priority**: From Issue #26 — enables structured PM workflows like "idea → brainstorm → generate PRD" with full traceability.

**Independent Test**: Can be fully tested by running a workflow from ideation to PRD generation and verifying traceability links between steps.

**Acceptance Scenarios**:

1. **Given** a PM workspace, **When** the user triggers an "Idea to PRD" workflow, **Then** the system guides through ideation, brainstorming, and PRD generation steps
2. **Given** a completed workflow, **When** the user views the traceability graph, **Then** they can see how the final PRD relates back to the original idea
3. **Given** a requirement document, **When** the user triggers "transform to test cases", **Then** the system generates test cases with links to originating requirements
4. **Given** a skill registry exists, **When** the user invokes a skill via `/pm-<id>` command, **Then** the corresponding workflow executes with proper data transformation

---

### User Story 5 - Fix Product Architecture Diagram (Priority: P3)

As a user, the product architecture diagram should correctly display and be interactive, showing the relationship between PM modules and agent capabilities.

**Why this priority**: Supporting feature — fixes existing broken functionality rather than adding new capabilities.

**Independent Test**: Can be fully tested by navigating to the architecture diagram page and verifying all nodes display correctly and are clickable.

**Acceptance Scenarios**:

1. **Given** the user navigates to the architecture diagram, **When** the page loads, **Then** all module nodes display without errors
2. **Given** the architecture diagram is displayed, **When** the user clicks on a module node, **Then** they see details about that module and its relationships
3. **Given** the architecture diagram includes agent capabilities, **When** the user clicks on an skill node, **Then** they see the skill definition and invocation methods
4. **Given** the diagram is interactive, **When** the user hovers over a connection, **Then** they see the data flow description between modules

---

### Edge Cases

- What happens when a workflow contains circular dependencies between nodes?
- How does the system handle data type mismatches between connected nodes?
- What happens when a workspace has no data but the agent is asked to perform an operation?
- How does the system handle agent write operations when the user declines confirmation? **Answer**: The operation is cancelled and the agent is notified. Partial state is NOT persisted.
- How does the system handle agent write operations when the session is in "allow all" mode but the operation is classified as dangerous (delete/overwrite)? **Answer**: Dangerous operations ALWAYS require confirmation, regardless of session settings. The system shows a confirmation modal and awaits user response.
- What happens when a workflow node fails mid-execution — is partial state preserved?
- How are concurrent edits to the same workflow handled?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a visual workflow canvas with draggable nodes representing workflow steps
- **FR-002**: System MUST allow users to connect nodes with directed edges representing data flow
- **FR-003**: System MUST support configuring data transformation rules per node, including both pre-defined node types (start, end, agent_call, data_transform, condition, loop, parallel_merge) and custom extension nodes registered via the skill registry
- **FR-004**: System MUST support session binding to PM workspaces, enabling agents to read workspace data
- **FR-005**: System MUST allow agents to read data from any PM workspace module when bound to a session
- **FR-006**: System MUST require human confirmation before agent-initiated write operations. **Strategy for this session: all writes in the current session are allowed by default (user can control via UI toggle); dangerous operations (delete, overwrite) ALWAYS require confirmation regardless of session setting.**
- **FR-007**: System MUST support fixed workflows (e.g., "Idea → PRD", "Requirements → Test Cases") with traceability
- **FR-008**: System MUST expose PM capabilities as reusable skills invocable via `/pm-<id>` commands
- **FR-009**: System MUST fix the product architecture diagram to display and interact correctly
- **FR-010**: System MUST show module relationships and data flows in the architecture diagram
- **FR-011**: System MUST support workspace switching mid-session with context updates
- **FR-012**: System MUST provide traceability links between workflow steps and generated outputs
- **FR-013**: System MUST handle workflow execution with proper error handling and state preservation
- **FR-014**: System MUST support multi-select of modules for cross-module operations
- **FR-015**: System MUST display skill definitions and invocation methods in the architecture diagram

### Key Entities *(include if feature involves data)*

- **Workflow**: Represents a visual workflow with nodes, edges, and configuration. Key attributes: id, name, nodes[], edges[], status, created_at, updated_at, execution_history[]
- **WorkflowNode**: Represents a single step in a workflow. Key attributes: id, type (enum: start | end | agent_call | data_transform | condition | loop | parallel_merge | custom), config, position_x, position_y, input_schema, output_schema, script (for custom nodes)
- **WorkflowEdge**: Represents data flow between nodes. Key attributes: id, source_node_id, target_node_id, data_mapping_rules
- **SessionBinding**: Represents a chat session bound to a PM workspace. Key attributes: session_id, workspace_id, bound_at
- **SkillContract**: Represents a reusable PM capability. Key attributes: id, name, description, outputContract, invocation, requiresConfirm
- **TraceabilityLink**: Represents relationships between workflow steps and outputs. Key attributes: id, source_entity_type, source_entity_id, target_entity_type, target_entity_id, confidence_score
- **ArchitectureNode**: Represents a module or skill in the architecture diagram. Key attributes: id, type, label, description, position, connections[]

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create and save a workflow with at least 5 nodes in under 3 minutes
- **SC-002**: Data flows correctly through connected nodes with 100% accuracy for defined transformation rules
- **SC-003**: Workspace-bound sessions can access and reference workspace data with response latency under 2 seconds
- **SC-004**: Agent-initiated write operations show confirmation prompt within 500ms
- **SC-005**: Fixed workflows (Idea→PRD, Requirements→Test Cases) complete successfully in 95% of attempts
- **SC-006**: Traceability links are generated automatically for all workflow outputs
- **SC-007**: Product architecture diagram loads without errors and all nodes are interactive
- **SC-008**: Skills are invocable via `/pm-<id>` commands with execution success rate above 90%
- **SC-009**: Users can switch workspaces mid-session without losing conversation context
- **SC-010**: Workflow execution handles errors gracefully, preserving partial state for recovery; complete execution history is retained for audit and replay

## Assumptions

- Users have a PM workspace created before using workflow or agent features
- The visual workflow designer is inspired by Dify but adapted for PM-specific use cases
- Agent capabilities build on Open WebUI's existing agent framework (Tools, Skills, Pipelines)
- The architecture diagram fix addresses existing rendering/interaction issues without requiring a complete redesign. **Scope limited to bug fixes only — no new features or integration with workflow designer.**
- Data transformations between workflow nodes follow a simple mapping syntax (field-to-field) for v1
- Human confirmation for agent writes is implemented as a modal dialog requiring explicit user action
- Workspace data access follows existing PM module permissions — no additional auth layer needed
- Skill registry is already partially implemented per Constitution §VI (Agent Platform Capabilities)
- Workflow execution runs entirely on the server side; the client is responsible only for the visual designer and status display
