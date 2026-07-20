# Feature Specification: Workflow Designer V2 - Global Access & AI Integration

**Feature Branch**: `[008-workflow-designer-v2]`

**Created**: 2026-07-11

**Status**: Draft

**Input**: User description: "1.路径错了。应该是和pm工作台同级。所有项目可以用。2.上手难度高。3.需要支持AI生成工作流。导入/导出为xml格式？4.工作流设计应该需要更全面店。5看看dify如何实现的。6输入输出的参数应该是有固定的以及自定义的。7.openwebui 的新对话里面应该支持直接用这些工作流，需要用个入口直接接入。8UI风格和Openwebui不统一"

## Clarifications

### Session 2026-07-11

- **Q**: 工作流入口位置 → **A**: 全局侧边栏（与 PM 工作台同级），所有项目可用
  - **影响**: 工作流设计器不应仅作为 PM 工作台子模块，而应作为全局功能，通过 OpenWebUI 侧边栏直接访问。支持跨项目复用工作流模板。
  - **已更新**: User Story 1（入口改为全局侧边栏）、Key Entities（新增 WorkflowTemplate 支持跨项目）
  
- **Q**: AI 生成工作流的具体方式 → **A**: 自然语言描述生成 + 模板推荐
  - **影响**: 用户可以通过自然语言描述需求，AI 自动生成工作流；同时系统根据使用场景推荐预置模板。生成后可手动调整。
  - **已更新**: User Story 2（AI 生成工作流）、Functional Requirements（FR-003）
  
- **Q**: AI 生成工作流的模型选择策略 → **A**: 使用用户当前配置的默认模型（Option B）
  - **影响**: AI 生成工作流时，使用用户在 OpenWebUI 中当前选择的默认模型，与现有模型选择机制保持一致，无需额外配置。
  - **已更新**: Functional Requirements（FR-003 明确模型选择策略）、Assumptions（新增 AI 生成假设）
  
- **Q**: 导入/导出格式 → **A**: XML + JSON 双格式
  
- **Q**: 输入输出参数类型 → **A**: 固定参数（预定义）+ 自定义参数（用户扩展）
  - **影响**: 每个节点有预定义的固定参数（如模型选择、温度等），同时支持用户添加自定义参数。参数类型包括：文本、数字、布尔、选择、文件、引用（上游节点输出）。
  - **已更新**: Key Entities（WorkflowNode 参数结构）、Functional Requirements（FR-004）
  
- **Q**: OpenWebUI 对话集成方式 → **A**: 侧边栏快捷入口 + 命令触发
  - **影响**: 在新建对话界面添加入口，用户可以直接选择已保存的工作流运行；同时支持通过 `/workflow-{id}` 命令触发。
  - **已更新**: User Story 5（对话集成）、Functional Requirements（FR-014）

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Global Workflow Access (Priority: P1)

As a user, I want to access the workflow designer from the global sidebar (same level as PM workspace), so that I can create and manage workflows for any project without navigating deep into PM modules.

**Why this priority**: This addresses the #1 user pain point — workflow designer is currently buried inside PM workspace, making it hard to discover and use. Making it globally accessible increases adoption and enables cross-project workflow reuse.

**Independent Test**: Can be fully tested by verifying the workflow designer is accessible from the global sidebar, and workflows created can be used across different projects.

**Acceptance Scenarios**:

1. **Given** the user is on any page in OpenWebUI, **When** they look at the global sidebar, **Then** they see a "Workflows" menu item at the same level as "PM Workspace"
2. **Given** the user clicks on "Workflows" in the sidebar, **When** the page loads, **Then** they see a list of existing workflows and a "Create New" button
3. **Given** the user is in Project A, **When** they create a workflow, **Then** they can use the same workflow in Project B without recreating it
4. **Given** the user has workflows created, **When** they search by name or tag, **Then** matching workflows are filtered in real-time

---

### User Story 2 - AI-Assisted Workflow Generation (Priority: P1)

As a user, I want to describe my workflow needs in natural language and have AI generate a complete workflow, so that I don't need to manually design complex workflows from scratch.

**Why this priority**: Addresses #2 pain point — high barrier to entry. AI generation lowers the learning curve and accelerates workflow creation, especially for non-technical users.

**Independent Test**: Can be fully tested by entering a natural language description (e.g., "Create a workflow that reads requirements and generates test cases") and verifying the generated workflow has appropriate nodes and connections.

**Acceptance Scenarios**:

1. **Given** the user is on the workflow designer, **When** they click "AI Generate" and enter "Create a content moderation pipeline", **Then** a workflow with nodes for input, processing, and output is generated
2. **Given** an AI-generated workflow, **When** the user reviews it, **Then** they can edit any node, add/remove connections, and adjust parameters before saving
3. **Given** the user has a partially designed workflow, **When** they select a group of nodes and ask AI to "optimize this section", **Then** the selected portion is refactored while preserving connections to other parts
4. **Given** the user has created multiple workflows, **When** they open the AI assistant, **Then** the system recommends templates based on their usage patterns and project type

---

### User Story 2b - Workflow Test Run & Debugging (Priority: P1)

As a user, I want to test-run my workflow directly in the designer before using it in production, so that I can verify it works correctly and debug issues.

**Why this priority**: Critical for workflow reliability — users need confidence that their workflow works before deploying it to chat or production.

**Independent Test**: Can be fully tested by creating a workflow and running it with test inputs, then verifying the execution trace and outputs.

**Acceptance Scenarios**:

1. **Given** a workflow is designed on the canvas, **When** the user clicks "Test Run", **Then** the workflow executes using OpenWebUI's configured model, and each node's execution status is shown in real-time
2. **Given** a workflow is running in test mode, **When** a node fails, **Then** the execution pauses, the failing node is highlighted, and the error message is displayed
3. **Given** a workflow test run completes, **When** the user reviews results, **Then** they can see the full execution trace: each node's input, output, and execution time
4. **Given** the user wants to debug a specific node, **When** they click on it in the execution trace, **Then** they can inspect the exact data that flowed through that node
5. **Given** a test run reveals an issue, **When** the user fixes the workflow and re-runs, **Then** the previous test inputs are preserved for quick re-testing

---

### User Story 3 - Comprehensive Node Library & Parameter System (Priority: P1)

As a user, I want a rich library of pre-built nodes with both fixed and custom parameters, so that I can build complex workflows without writing code.

**Why this priority**: Addresses #4 and #6 — current node library is limited and parameter system is not flexible enough. A comprehensive node library with flexible parameters enables more sophisticated workflows.

**Independent Test**: Can be fully tested by building a workflow that uses at least 5 different node types, configures both fixed and custom parameters, and successfully executes.

**Acceptance Scenarios**:

1. **Given** the workflow designer is open, **When** the user opens the node sidebar, **Then** they see categorized nodes: Input/Output, AI/LLM, Data Processing, Logic/Control, Integrations, PM Modules
2. **Given** the user drags an "LLM Call" node to the canvas, **When** they open its configuration, **Then** they see fixed parameters (model, temperature, max_tokens) and can add custom parameters (headers, custom fields)
3. **Given** a node with custom parameters, **When** the user defines a new parameter with type "Reference", **Then** they can select outputs from upstream nodes as input values
4. **Given** the user builds a workflow with a "Condition" node, **When** they configure branching logic, **Then** they can use expressions like `{{node1.output.score}} > 0.8` to determine the branch

---

### User Story 4 - Import/Export & Interoperability (Priority: P2)

As a user, I want to import and export workflows in standard formats (XML/JSON), so that I can share workflows with others and integrate with external tools.

**Why this priority**: Addresses #3 — import/export enables workflow sharing, version control, and integration with external systems. XML format specifically enables BPMN compatibility.

**Independent Test**: Can be fully tested by exporting a workflow to XML, importing it back, and verifying all nodes, edges, and configurations are preserved.

**Acceptance Scenarios**:

1. **Given** a completed workflow, **When** the user clicks "Export" and selects "XML (BPMN)", **Then** a `.bpmn` file is downloaded containing the full workflow definition
2. **Given** a BPMN file from another tool, **When** the user imports it, **Then** the system recognizes the format and maps compatible nodes (start, end, task, gateway) to internal node types
3. **Given** a workflow with unsupported BPMN elements, **When** the user imports it, **Then** unsupported elements are flagged with warnings, and the rest of the workflow is imported successfully
4. **Given** the user exports a workflow to JSON, **When** they share the file with another user, **Then** the recipient can import it and get an identical workflow including custom parameters

---

### User Story 5 - OpenWebUI Chat Integration & Execution (Priority: P2)

As a user, I want to trigger workflows directly from the chat interface and see the full execution process and results, so that I can use my designed workflows as part of conversations without switching contexts.

**Why this priority**: Addresses #7 — seamless integration with OpenWebUI's core chat experience makes workflows more accessible and useful in daily workflows. Users need to see not just the final result but the entire execution process for transparency and debugging.

**Independent Test**: Can be fully tested by starting a new chat, selecting a workflow, and verifying it executes correctly with the conversation context, showing execution trace and final results.

**Acceptance Scenarios**:

1. **Given** the user is in a new chat, **When** they click a workflow button in the chat input area, **Then** a dropdown shows available workflows they can select
2. **Given** the user selects a workflow in chat, **When** they send a message, **Then** the workflow executes using the message as input, and results are streamed back into the chat
3. **Given** a workflow is running in chat, **When** the user wants to stop it, **Then** they can click a stop button, and the workflow halts gracefully
4. **Given** the user frequently uses a specific workflow, **When** they pin it, **Then** it appears as a quick-access button in the chat interface
5. **Given** a workflow is executing in chat, **When** each node runs, **Then** the user sees real-time execution status: node name, execution time, and intermediate outputs
6. **Given** a workflow execution completes in chat, **When** the final node produces output, **Then** the result is displayed in the chat with clear formatting (text, JSON, or structured data)
7. **Given** a workflow execution fails in chat, **When** an error occurs, **Then** the error is shown with the failing node highlighted, error message, and suggestion to fix the workflow in the designer

---

### User Story 6 - Unified UI Style (Priority: P3)

As a user, I want the workflow designer to visually match the rest of OpenWebUI, so that the experience feels cohesive and familiar.

**Why this priority**: Addresses #8 — UI inconsistency creates cognitive friction. While important, this can be incrementally improved and doesn't block core functionality.

**Independent Test**: Can be fully tested by comparing the workflow designer's visual elements (colors, typography, spacing, components) with other OpenWebUI pages and verifying consistency.

**Acceptance Scenarios**:

1. **Given** the user switches between the chat page and workflow designer, **When** they compare the UI, **Then** colors, fonts, buttons, and inputs follow the same design system
2. **Given** the user is in dark mode, **When** they open the workflow designer, **Then** all elements adapt correctly with appropriate contrast and colors
3. **Given** the user resizes the browser window, **When** the workflow designer adjusts, **Then** the layout is responsive and usable at different screen sizes

---

### Edge Cases

- What happens when an AI-generated workflow contains circular dependencies?
- How does the system handle importing a workflow with node types that don't exist in the current system?
- What happens when a workflow references a model that is no longer available?
- How does the system handle concurrent edits to the same workflow by multiple users?
- What happens when a workflow execution exceeds the maximum allowed time?
- How are parameter type mismatches between connected nodes handled?
- What happens when a user tries to export a workflow with unsaved changes?
- How does the system handle workflow templates that reference project-specific resources when used in a different project?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a global "Workflows" entry point in the OpenWebUI sidebar, at the same level as "PM Workspace"
- **FR-002**: System MUST support creating, editing, saving, and deleting workflows from the global workflow page
- **FR-003**: System MUST support AI-generated workflow creation from natural language descriptions, with the ability to edit before saving
- **FR-004**: System MUST provide a comprehensive node library with categorized pre-built nodes (Input/Output, AI/LLM, Data Processing, Logic/Control, Integrations, PM Modules)
- **FR-005**: System MUST support both fixed parameters (defined by node type) and custom parameters (user-defined) for each node
- **FR-006**: System MUST support parameter types: Text, Number, Boolean, Select, File, Reference (to upstream node outputs)
- **FR-007**: System MUST allow connecting nodes with directed edges representing data flow, with validation for compatible types
- **FR-008**: System MUST support conditional branching with expression-based logic (e.g., `{{node.output}} > threshold`)
- **FR-009**: System MUST support looping constructs for iterative processing
- **FR-010**: System MUST support parallel execution and aggregation of results
- **FR-011**: System MUST allow exporting workflows to XML (BPMN-compatible) and JSON formats
- **FR-012**: System MUST allow importing workflows from XML (BPMN) and JSON formats, with graceful handling of unsupported elements
- **FR-013**: System MUST provide a chat integration that allows selecting and running workflows from the OpenWebUI chat interface, with real-time execution trace visible to the user
- **FR-014**: System MUST support triggering workflows via chat commands (e.g., `/workflow-{id}`)
- **FR-015**: System MUST support pinning frequently used workflows for quick access in chat
- **FR-016**: System MUST display workflow execution progress in chat: node-by-node status, intermediate outputs, and final results
- **FR-017**: System MUST allow test-running workflows in the designer with test inputs, showing execution trace and outputs for debugging
- **FR-018**: System MUST use OpenWebUI's existing design system (colors, typography, components) for visual consistency
- **FR-019**: System MUST support dark mode and responsive layouts
- **FR-020**: System MUST provide real-time validation and error feedback during workflow design
- **FR-021**: System MUST support workflow versioning (save multiple versions of the same workflow)
- **FR-022**: System MUST support workflow templates (pre-built workflows that can be cloned and customized)

### Key Entities *(include if feature involves data)*

- **Workflow**: Represents a visual workflow. Key attributes: id, name, description, nodes[], edges[], version, status (draft/active/archived), created_at, updated_at, owner_id, project_ids[] (for cross-project sharing), tags[]
- **WorkflowNode**: Represents a single step. Key attributes: id, type (enum: start | end | llm_call | agent_call | data_transform | condition | loop | parallel | merge | webhook | pm_module | custom), config{}, position {x, y}, parameters[] (fixed + custom), input_schema, output_schema
- **WorkflowEdge**: Represents data flow. Key attributes: id, source_node_id, source_port, target_node_id, target_port, data_mapping (field mapping between nodes)
- **NodeParameter**: Represents a configurable parameter. Key attributes: id, name, type (text|number|boolean|select|file|reference), required, default_value, options[] (for select), validation_rules[], description
- **WorkflowTemplate**: Represents a reusable template. Key attributes: id, name, description, workflow_definition, category, usage_count, rating
- **WorkflowExecution**: Represents a workflow run. Key attributes: id, workflow_id, status, started_at, completed_at, triggered_by, input_data, output_data, execution_log[]
- **WorkflowExport**: Represents an export/import record. Key attributes: id, workflow_id, format (xml|json), content, exported_at

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a basic workflow (3+ connected nodes) in under 2 minutes
- **SC-002**: AI-generated workflows require manual editing in less than 30% of cases (high quality generation)
- **SC-003**: Exported XML files are valid BPMN 2.0 and can be imported by at least 2 popular tools (e.g., Camunda, Bizagi)
- **SC-004**: Workflows can be accessed and used across projects without recreation
- **SC-005**: Chat integration allows triggering workflows in under 3 clicks from the chat interface
- **SC-006**: Workflow designer UI passes visual consistency audit with OpenWebUI design system (color, typography, spacing match within 5% tolerance)
- **SC-007**: Parameter configuration supports at least 6 types (text, number, boolean, select, file, reference)
- **SC-008**: Workflow execution success rate is above 95% for workflows with up to 20 nodes
- **SC-009**: Import/export roundtrip preserves 100% of node configurations and connections
- **SC-010**: Users can discover and access the workflow designer from any page in under 2 clicks
- **SC-011**: Test-run in designer shows execution trace with node-level status, inputs, and outputs
- **SC-012**: Chat execution displays real-time node status with intermediate outputs visible to user

## Assumptions

- Users are familiar with basic workflow concepts (nodes, connections, data flow)
- The AI generation feature uses the existing OpenWebUI LLM integration, specifically the user's currently selected default model (no separate model configuration needed)
- BPMN import/export focuses on core elements (start, end, task, gateway, sequence flow); complex BPMN features may not be fully supported in v1
- Cross-project workflow sharing respects existing project permissions and access controls
- Chat integration reuses the existing OpenWebUI chat infrastructure (WebSocket, message rendering)
- The design system alignment leverages existing Tailwind CSS configuration and component library
- Workflow execution runs server-side with the existing Python backend infrastructure, using OpenWebUI's configured models for LLM/Agent nodes
- Test-run in designer uses the same execution engine as chat execution, with test inputs provided by the user
- Chat execution streams node-by-node progress via WebSocket, showing intermediate outputs in real-time
- Custom node types can be registered via the existing skill/plugin system
