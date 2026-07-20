# Feature Specification: Timbal-OpenWebUI Integration

**Feature Branch**: `[001-timbal-openwebui-integration]`

**Created**: 2026-07-12

**Status**: Draft

**Input**: User description: "根据方案1+2实现timbal和openwebui的实现，尽量全面、参考dify的工作流实现。把平台的pm节点、openwebui节点的参数、功能、输入输出都能覆盖到"

## Clarifications

### Session 2026-07-12

- **Q**: TimbalExecution 应该支持哪些状态，以及状态之间的流转规则是什么？
  **A**: 类 Dify 状态机模型（pending → running → succeeded/failed/stopped），支持手动停止和自动超时。
- **Q**: 当 Timbal 服务不可用时，系统应该采用什么降级策略？
  **A**: 完全失败：直接显示错误页面，所有工作流功能不可用。
- **Q**: Timbal 工具调用失败时的重试策略是什么？
  **A**: 指数退避重试：最多重试 3 次，间隔 1s、2s、4s，失败后返回错误。
- **Q**: 工作流版本控制应该采用什么策略？
  **A**: Git 式版本：基于 commit hash 追踪，支持分支和合并。
- **Q**: 用户权限模型应该如何设计？谁可以执行/编辑/删除工作流？
  **A**: 完全开放：所有用户都可以执行、编辑、删除任何工作流。
- **Q**: Agent 应该如何绑定 OpenWebUI 的 skills、prompts 和 tools？
  **A**: 通过配置映射 + 插件系统：在 Timbal 工作流节点配置中，允许用户选择绑定的 OpenWebUI skill/prompt/tool（配置映射），同时开发独立的插件桥接层，OpenWebUI 和 Timbal 通过插件协议通信（插件系统）。
- **Q**: PM 工作台的参数结构应该如何映射到 Timbal 工具的输入参数？
  **A**: 自动映射 + 手动覆盖 + 模板驱动：系统自动将 PM 实体字段映射为 Timbal 工具参数（自动映射），同时允许用户手动调整映射关系（手动覆盖），并提供预定义的参数映射模板供用户选择（模板驱动）。
- **Q**: 工作流的调用协议应该是什么样的？支持哪些调用方式？
  **A**: 多协议支持 + 聊天集成：REST API（同步/异步）、SSE 流式、WebSocket 实时（多协议支持），以及 OpenWebUI 聊天命令触发（聊天集成）。
- **Q**: 工作流的输入输出格式应该是什么？如何与 OpenWebUI 的上下文（conversation history、user profile 等）交互？
  **A**: 标准化 JSON + 上下文注入 + 对象格式 + 模板格式：工作流输入输出使用标准 JSON Schema（标准化 JSON），系统自动注入 OpenWebUI 上下文如 conversation history、user profile、当前项目等（上下文注入），支持特定对象结构自定义解析（对象格式），以及模板字符串变量插值（模板格式）。
- **Q**: 工作流执行结果如何反馈到 OpenWebUI 的聊天界面？支持哪些展示格式？
  **A**: 多格式支持 + 结构化卡片：文本、Markdown 表格、JSON 折叠面板、图片、文件下载链接、交互式组件（多格式支持），以及类 Notion 的卡片式布局展示结果（结构化卡片）。

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.

  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently
-->

### User Story 1 - Timbal Workflow Execution from OpenWebUI (Priority: P1)

As a platform user, I want to execute Timbal workflows directly from the OpenWebUI interface so that I can leverage Timbal's Python-based workforce capabilities without leaving the OpenWebUI environment.

**Why this priority**: This is the core integration feature that enables the entire Timbal-OpenWebUI ecosystem. Without workflow execution, the integration provides no value.

**Independent Test**: Can be fully tested by configuring a Timbal endpoint and triggering a workflow run from the OpenWebUI chat interface or workflow page.

**Acceptance Scenarios**:

1. **Given** a user types "/workflow run risk-analysis" in chat, **When** the command is recognized, **Then** the corresponding Timbal workflow executes and results are streamed back to the chat.
2. **Given** a user triggers a workflow via REST API with `?sync=true`, **When** the workflow completes, **Then** the full result is returned in the HTTP response.
3. **Given** a user triggers a workflow via REST API with `?sync=false`, **When** the workflow starts, **Then** an execution ID is returned immediately and the user can poll for status.
2. **Given** a Timbal workflow is running, **When** the user views the workflow status, **Then** real-time updates are streamed via SSE to show progress.
3. **Given** a Timbal workflow execution fails, **When** the error occurs, **Then** the user sees a clear error message with actionable details.

---

### User Story 2 - PM Workspace Nodes as Timbal Tools (Priority: P1)

As a product manager, I want PM workspace capabilities (project data, requirements, documents) to be exposed as Timbal tools/nodes so that Timbal workflows can interact with PM data programmatically.

**Why this priority**: This enables the bidirectional integration where Timbal can read from and write to the PM workspace, making the integration truly useful for PM workflows.

**Independent Test**: Can be fully tested by defining a Timbal tool that fetches project data and verifying it returns correct PM workspace information.

**Acceptance Scenarios**:

1. **Given** a Timbal workflow defines a tool call for "get_project_list", **When** the tool executes, **Then** it returns the list of projects from the PM workspace.
2. **Given** a Timbal workflow defines a tool call for "create_requirement", **When** the tool executes with valid parameters, **Then** a new requirement is created in the PM workspace.
3. **Given** a Timbal tool call fails due to missing project_id, **When** the error propagates, **Then** Timbal receives a structured error response that can be handled in the workflow logic.

---

### User Story 3 - OpenWebUI Chat Integration with Timbal (Priority: P2)

As an OpenWebUI user, I want to invoke Timbal workflows through natural language in the chat interface so that I can trigger complex PM operations conversationally.

**Why this priority**: This provides a natural user experience for triggering workflows, but it depends on the core execution and tool integration features.

**Independent Test**: Can be fully tested by typing a natural language command in chat that maps to a Timbal workflow and verifying the workflow executes correctly.

**Acceptance Scenarios**:

1. **Given** a user types "analyze project risks for Project Alpha" in chat, **When** the system recognizes this as a Timbal workflow trigger, **Then** the corresponding risk analysis workflow executes.
2. **Given** a workflow requires project selection, **When** the user is prompted to choose from available projects, **Then** a dropdown or interactive element appears in the chat.
3. **Given** a workflow produces structured output, **When** results are returned, **Then** they are formatted appropriately in the chat interface (tables, lists, etc.).

---

### User Story 4 - Visual Workflow Designer for Timbal (Priority: P2)

As a workflow designer, I want to create and edit Timbal workflows using a visual drag-and-drop interface so that I don't need to write Python code to define workflows.

**Why this priority**: This democratizes workflow creation for non-technical users, but it requires the underlying execution engine to be functional first.

**Independent Test**: Can be fully tested by creating a workflow visually, saving it, and executing it successfully.

**Acceptance Scenarios**:

1. **Given** a user drags a "PM Data Source" node onto the canvas, **When** they configure it with a project ID, **Then** the node is validated and connected to the workflow.
2. **Given** a user connects a "Get Requirements" node to an "Analyze" node, **When** the workflow executes, **Then** the output of the first node feeds into the second.
3. **Given** a user saves a workflow definition, **When** they reload the page, **Then** the workflow layout and configuration are preserved.

---

### User Story 5 - Workflow Management Dashboard (Priority: P3)

As an administrator, I want to view and manage all Timbal workflows from a centralized dashboard so that I can monitor usage and troubleshoot issues.

**Why this priority**: This is an operational feature that enhances manageability but is not required for core functionality.

**Independent Test**: Can be fully tested by navigating to the workflows page and verifying all CRUD operations work.

**Acceptance Scenarios**:

1. **Given** the user navigates to the Workflows page, **When** the page loads, **Then** a list of available workflows is displayed with status indicators.
2. **Given** a workflow is running, **When** the user views the workflow details, **Then** execution logs and current status are shown in real-time.
3. **Given** a user wants to disable a workflow, **When** they toggle the workflow status, **Then** the workflow is no longer executable but remains in the list.

---

### Edge Cases

- What happens when the Timbal service is unreachable? → System should show a clear error page indicating the Timbal service is unavailable. All workflow execution features are disabled until the service recovers. Users can still view historical execution logs and workflow definitions.
- How does the system handle a Timbal workflow that runs longer than the HTTP timeout? → Use SSE streaming for long-running workflows.
- What happens when a Timbal tool returns malformed data? → Validate tool outputs and show structured error messages.
- How does the system handle concurrent workflow executions? → Each execution should be isolated with its own execution ID.
- What happens when a workflow references a deleted PM project? → Return a clear error indicating the project no longer exists.
- What happens when a user tries to stop a workflow that has already completed? → Return a clear error indicating the workflow is already in a terminal state.
- What happens when a workflow execution exceeds the configured timeout? → Automatically transition to `failed` status with a timeout error message.
- What happens when a user stops a workflow mid-execution? → Transition to `stopped` status, preserve partial outputs and logs, and notify Timbal to terminate the workforce process.

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: The system MUST provide a Timbal API client that supports `POST /run`, `POST /stream`, and `GET /healthcheck` endpoints.
- **FR-001a**: The system MUST support multiple invocation protocols: REST API (synchronous and asynchronous), Server-Sent Events (SSE) for streaming results, and WebSocket for real-time bidirectional communication.
- **FR-001b**: The system MUST allow workflows to be triggered from the OpenWebUI chat interface via natural language commands or explicit slash commands (e.g., `/workflow run <workflow-name>`).
- **FR-002**: The system MUST expose PM workspace operations (projects, requirements, documents, test cases) as Timbal-compatible tool definitions.
- **FR-002a**: The system MUST support binding OpenWebUI skills, prompts, and tools to Timbal workflow nodes via configuration mapping. Users MUST be able to select which OpenWebUI resources are available to each workflow node.
- **FR-002b**: The system MUST provide a plugin bridge layer that allows OpenWebUI and Timbal to communicate through a standardized plugin protocol, enabling extensible integration without core code changes.
- **FR-003**: Users MUST be able to trigger Timbal workflows from the OpenWebUI chat interface via natural language or explicit commands.
- **FR-004**: The system MUST support real-time workflow status updates via Server-Sent Events (SSE) for long-running workflows.
- **FR-005**: The system MUST provide a visual workflow designer (SvelteFlow-based) for creating and editing workflows independently of PM projects.
- **FR-006**: The system MUST support workflow configuration including Timbal endpoint URL, API keys, and timeout settings.
- **FR-007**: The system MUST display workflow execution results in a user-friendly format within the OpenWebUI interface. Supported formats include: plain text, Markdown tables, collapsible JSON panels, images, file download links, and interactive components (buttons, dropdowns). Results MAY also be rendered as structured cards (Notion-style layouts) for complex data.
- **FR-008**: The system MUST handle Timbal workflow errors gracefully with clear user-facing error messages. Tool call failures MUST be retried with exponential backoff (max 3 retries: 1s, 2s, 4s intervals) before surfacing the error to the user.
- **FR-009**: The system MUST support bidirectional data flow: OpenWebUI/PM data can be inputs to Timbal workflows, and workflow outputs can update PM data.
- **FR-010**: The system MUST provide a workflow management page listing all workflows with CRUD operations. All authenticated users have full execute/edit/delete permissions on all workflows (open permissions model).
- **FR-011**: The system MUST support workflow versioning so users can track changes and roll back to previous versions.
- **FR-012**: The system MUST validate workflow definitions before execution to catch configuration errors early.

### Key Entities *(include if feature involves data)*

- **TimbalWorkflow**: Represents a workflow definition including nodes, edges, configuration, and metadata. Attributes: id, name, description, nodes[], edges[], config{}, version, created_at, updated_at.
  - **Versioning Strategy**: Git-style versioning based on commit hash tracking. Each save creates a new commit with a unique hash. Supports branching (draft versions) and merging (publishing). Users can view the full version history, compare diffs between versions, and roll back to any previous commit.
  - **Input/Output Format**:
    - **Standard JSON Schema**: All workflow inputs and outputs MUST conform to JSON Schema for validation and interoperability
    - **Context Injection**: The system automatically injects OpenWebUI context into workflow inputs, including: conversation history, user profile, current project, active model settings
    - **Object Format**: Supports structured objects with custom parsing rules for complex data types
    - **Template Format**: Supports template strings with variable interpolation (e.g., `{{user.name}}`, `{{project.id}}`) for dynamic input generation
- **TimbalExecution**: Represents a single workflow execution instance. Attributes: id, workflow_id, status (pending|running|succeeded|failed|stopped), inputs{}, outputs{}, logs[], started_at, completed_at, error_message, stopped_by, timeout_at.
  - **Status Transitions**:
    - `pending` → `running`: When execution starts
    - `running` → `succeeded`: When workflow completes successfully
    - `running` → `failed`: When workflow encounters an error
    - `running` → `stopped`: When user manually stops the execution
    - `pending` → `failed`: When execution fails to start (e.g., validation error)
    - `running` → `failed`: When execution exceeds timeout_at
- **TimbalTool**: Represents a tool definition that maps to a PM workspace operation. Attributes: name, description, parameters{}, return_schema{}, handler_function.
  - **Binding Types**:
    - `pm_operation`: Direct PM workspace CRUD operations (projects, requirements, documents, test cases)
    - `openwebui_skill`: OpenWebUI skills (e.g., code generation, document analysis)
    - `openwebui_prompt`: Pre-defined prompts from OpenWebUI prompt library
    - `openwebui_tool`: Native OpenWebUI tools (e.g., web search, image generation)
  - **Plugin Protocol**: Tools using the plugin bridge MUST implement a standard interface: `initialize(config) → void`, `execute(inputs) → outputs`, `validate(parameters) → boolean`. The plugin bridge handles authentication, request routing, and response formatting between Timbal and OpenWebUI.
- **TimbalNode**: Represents a node in the workflow graph. Attributes: id, type, config{}, inputs[], outputs[], position{x, y}.
  - **PM Parameter Mapping**: Nodes that interact with PM workspace MUST support parameter mapping:
    - **Auto-mapping**: System automatically maps PM entity fields (e.g., `project.name`, `requirement.title`) to node input parameters based on entity schema
    - **Manual override**: Users can manually adjust auto-mapped parameters or define custom mappings
    - **Template-driven**: Pre-defined mapping templates for common PM operations (e.g., "Create Requirement", "Update Project Status")
- **TimbalConfig**: Represents system-wide Timbal integration settings. Attributes: endpoint_url, api_key, timeout, max_concurrent_executions.

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: Users can execute a Timbal workflow from OpenWebUI and see results within 5 seconds for simple workflows.
- **SC-002**: 95% of Timbal workflow executions complete successfully when the Timbal service is healthy.
- **SC-003**: Users can create a visual workflow with at least 5 nodes without writing code.
- **SC-004**: Workflow execution status updates are displayed in real-time with less than 1 second latency.
- **SC-005**: All PM workspace operations exposed as Timbal tools return valid data within 3 seconds.
- **SC-006**: Users can view execution history and logs for any workflow run within 2 seconds of navigation.
- **SC-007**: The system handles Timbal service unavailability gracefully, showing clear error messages within 2 seconds.

## Assumptions

- Timbal service is accessible via HTTP/HTTPS from the OpenWebUI backend.
- Timbal's API contract (endpoints, request/response formats) remains stable during implementation.
- OpenWebUI's existing authentication system can be extended to authorize Timbal workflow executions.
- PM workspace data schema is stable enough to expose as Timbal tool interfaces.
- Users have sufficient permissions to access both OpenWebUI and Timbal services.
- The visual workflow designer (SvelteFlow) can be extended to support Timbal-specific node types without major refactoring.
