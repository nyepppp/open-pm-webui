# Feature Specification: Flowchart Rebuild

**Feature Branch**: `[001-flowchart-rebuild]`

**Created**: 2026-07-10

**Status**: Draft

**Input**: User description: "重构流程图功能。目前功能很不完善。https://x6.antv.antgroup.com/tutorial/getting-started 需要根据文档吧所有功能都富含到；基础；插件；进阶。并且保留绑定参数和功能模块节点的功能"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Flowchart Creation (Priority: P1)

As a user, I want to create flowcharts by dragging and dropping nodes, connecting them with edges, and editing their properties, so that I can visually design workflows.

**Why this priority**: This is the foundational capability. Without basic node/edge creation and editing, the flowchart feature is unusable.

**Independent Test**: Can be fully tested by opening the flowchart editor, adding nodes, connecting them, and verifying the visual output.

**Acceptance Scenarios**:

1. **Given** the flowchart editor is open, **When** I drag a node from the palette to the canvas, **Then** a new node appears at the drop location.
2. **Given** two nodes exist on the canvas, **When** I click and drag from one node's output port to another's input port, **Then** an edge is created connecting them.
3. **Given** a node is selected, **When** I edit its text label, **Then** the label updates in real-time.

---

### User Story 2 - Parameter and Module Node Binding (Priority: P1)

As a user, I want to bind specific nodes (e.g., parameter nodes, functional module nodes) to external data or logic, so that the flowchart represents a dynamic, executable workflow rather than just a static diagram.

**Why this priority**: This is a core existing feature that must be preserved. It differentiates this flowchart from a simple drawing tool.

**Independent Test**: Can be fully tested by creating a parameter node, binding it to a data source, and verifying that the binding is persisted and displayed.

**Acceptance Scenarios**:

1. **Given** a parameter node exists, **When** I configure its binding to a specific data field, **Then** the binding is saved and the node displays the bound value.
2. **Given** a functional module node exists, **When** I link it to a specific module, **Then** the node's properties reflect the linked module's configuration.
3. **Given** a bound node, **When** the underlying data changes, **Then** the node updates to reflect the new data (if real-time updates are supported).

---

### User Story 3 - Advanced Layout and Routing (Priority: P2)

As a user, I want the flowchart to automatically arrange nodes in a clean, readable layout and route edges to avoid overlaps, so that I don't have to manually position every element.

**Why this priority**: Manually positioning nodes is tedious and error-prone. Automatic layout significantly improves the user experience for complex diagrams.

**Independent Test**: Can be fully tested by creating a complex flowchart with many nodes and edges, triggering the auto-layout function, and verifying that nodes are neatly arranged and edges do not overlap.

**Acceptance Scenarios**:

1. **Given** a flowchart with 10+ nodes in random positions, **When** I trigger the auto-layout feature, **Then** all nodes are repositioned according to a defined algorithm (e.g., hierarchical, grid).
2. **Given** two nodes are connected by an edge, **When** I move one node, **Then** the edge updates its path to maintain a clear connection without crossing other nodes.

---

### User Story 4 - Plugin and Extension Support (Priority: P2)

As a user, I want to extend the flowchart's capabilities through plugins (e.g., custom node types, validation rules, export formats), so that the tool can adapt to my specific needs.

**Why this priority**: Plugins allow the flowchart to be used in diverse contexts. This aligns with the requirement to cover X6's plugin capabilities.

**Independent Test**: Can be fully tested by installing a plugin that adds a new node type, creating a node of that type, and verifying its unique behavior.

**Acceptance Scenarios**:

1. **Given** a plugin is registered, **When** I open the node palette, **Then** the new node types provided by the plugin are available.
2. **Given** a custom validation plugin is active, **When** I create a flowchart that violates the plugin's rules, **Then** the invalid elements are highlighted with error messages.

---

### User Story 5 - Export and Collaboration (Priority: P3)

As a user, I want to export my flowchart as an image or JSON file and share it with my team, so that we can collaborate on workflow designs.

**Why this priority**: Collaboration and sharing are important but not core to the basic functionality. They can be built on top of the existing features.

**Independent Test**: Can be fully tested by creating a flowchart, clicking the export button, and verifying that a valid file is downloaded.

**Acceptance Scenarios**:

1. **Given** a flowchart is complete, **When** I select "Export as PNG", **Then** a PNG image of the current canvas view is downloaded.
2. **Given** a flowchart is complete, **When** I select "Export as JSON", **Then** a JSON file containing all nodes, edges, and their properties is downloaded.
3. **Given** a JSON file from a previous export, **When** I import it, **Then** the flowchart is restored to its previous state.

---

### Edge Cases

- What happens when a user tries to connect two nodes that are already connected?
  - **Expected**: The system allows or prevents duplicate connections based on the `allowMulti` configuration. If `allowMulti` is false, the second connection attempt is blocked with visual feedback.
- How does the system handle a very large flowchart (e.g., 500+ nodes) in terms of performance?
  - **Expected**: The canvas uses virtual rendering to only render visible nodes/edges, maintaining at least 30 FPS during pan/zoom. Large flowcharts may trigger a performance warning but remain editable.
- What happens if a user deletes a node that has edges connected to it?
  - **Expected**: All connected edges are automatically removed when the node is deleted. The user is NOT prompted for confirmation unless the node has bound data (parameter/module binding).
- How does the system handle invalid data when importing a flowchart JSON?
  - **Expected**: Invalid data is rejected with a clear error message indicating which nodes/edges failed validation. Valid portions of the data are imported; invalid portions are skipped with a log of errors.
- What is the behavior when a user zooms in/out extensively on the canvas?
  - **Expected**: Zoom is constrained to a minimum of 10% and maximum of 500%. At extreme zoom levels, labels may be hidden to maintain readability. The canvas remains pannable at all zoom levels.

## Requirements *(mandatory)*

### Functional Requirements

#### Basic (基础功能)

- **FR-001**: The system MUST provide a canvas (Graph) for users to create and manipulate flowchart elements (nodes and edges), supporting configurable width, height, background color, and grid.
- **FR-002**: The system MUST support basic node types (e.g., start, end, process, decision) that can be dragged onto the canvas, with support for custom shapes (rect, circle, ellipse, polygon, image, HTML) via markup and attrs.
- **FR-003**: The system MUST allow users to create directed edges between nodes by connecting output ports to input ports, with support for source/target configuration, vertices (path points), router (normal, orth, oneSide, manhattan, metro, er), and connector (normal, rounded, smooth, jumpover).
- **FR-004**: The system MUST support editing node properties, including text labels, colors, sizes, and custom attrs via prop() and attr() APIs.
- **FR-005**: The system MUST support connection ports (连接桩) on nodes, including port groups, individual port configuration, and dynamic port addition/removal/update.
- **FR-006**: The system MUST support interactive connecting with configurable rules (allowBlank, allowLoop, allowNode, allowEdge, allowPort, allowMulti) and validation (validateMagnet, validateConnection, validateEdge).
- **FR-007**: The system MUST support embedding (组合) nodes by dragging one node into another to create parent-child relationships.
- **FR-008**: The system MUST support highlighting configurations for different interaction states (magnetAvailable, magnetAdsorbed, embedding, nodeAvailable).
- **FR-009**: The system MUST provide zoom and pan capabilities on the canvas, with configurable mousewheel and panning behavior.
- **FR-010**: The system MUST support data serialization (toJSON/fromJSON) for persisting and restoring flowchart state.
- **FR-011**: The system MUST support animation on nodes and edges, including position, size, and custom property animations.

#### Plugin (插件功能)

- **FR-012**: The system MUST support the Transform plugin for resizing and rotating nodes via interactive widgets.
- **FR-013**: The system MUST support the Snapline plugin for alignment assistance when moving nodes.
- **FR-014**: The system MUST support the Clipboard plugin for copy/paste operations, including localStorage persistence.
- **FR-015**: The system MUST support the Keyboard plugin for custom keyboard shortcuts and hotkeys.
- **FR-016**: The system MUST support the History plugin for undo/redo operations, with configurable stack size and batch updates.
- **FR-017**: The system MUST support the Selection plugin for single/multi-select, rubberband (框选), and moving selected nodes.
- **FR-018**: The system MUST support the Scroller plugin for scrollable canvas with pagination and auto-resize.
- **FR-019**: The system MUST support the MiniMap plugin for an overview map of the entire canvas.
- **FR-020**: The system MUST support the Dnd plugin for dragging nodes from external sources onto the canvas.
- **FR-021**: The system MUST support the Stencil plugin for a sidebar palette with grouped, collapsible, and searchable node templates.
- **FR-022**: The system MUST support the Export plugin for exporting the canvas as PNG, JPEG, or SVG.

#### Advanced (进阶功能)

- **FR-023**: The system MUST support custom connection points (anchor) and connection points (connectionPoint) for precise edge attachment control.
- **FR-024**: The system MUST support tools on nodes and edges, including built-in tools (button, button-remove, boundary, vertices, segments, source-arrowhead, target-arrowhead).
- **FR-025**: The system MUST support groups with parent-child relationships, including expand/collapse functionality and automatic parent resizing.
- **FR-026**: The system MUST support custom node rendering using React, Vue, Angular, or HTML components, with data binding and update mechanisms.
- **FR-027**: The system MUST support custom edge rendering with labels, arrows (block, classic, diamond, cross, async, path, circle, circlePlus, ellipse), and custom markers.
- **FR-028**: The system MUST support custom node shapes and edge styles via markup and attrs configuration.
- **FR-029**: The system MUST support custom routers and connectors for advanced edge routing algorithms.
- **FR-030**: The system MUST support custom highlighters for visual feedback during interactions.
- **FR-031**: The system MUST support custom port layouts and label positions.
- **FR-032**: The system MUST support custom tools for nodes and edges.

#### Parameter and Module Node Binding (保留功能)

- **FR-033**: The system MUST support parameter binding for specific node types, allowing nodes to display or interact with external data.
- **FR-034**: The system MUST support functional module node binding, allowing nodes to represent and link to specific functional modules.
- **FR-035**: The system MUST support traceability binding, allowing nodes to be bound to PRD, module, feature, or parameter entities.
- **FR-036**: The system MUST support input/output parameter configuration on nodes.
- **FR-037**: The system MUST support traceability badges on nodes to visually indicate binding status.

#### Import/Export and Collaboration

- **FR-038**: The system MUST allow users to export flowcharts as images (PNG, SVG) and structured data (JSON).
- **FR-039**: The system MUST allow users to import flowcharts from structured data (JSON).
- **FR-040**: The system MUST support keyboard shortcuts for common actions (e.g., delete, copy, paste).
- **FR-041**: The system MUST provide visual feedback for user interactions (e.g., hover effects, selection highlights, connection previews).

### Key Entities

- **Flowchart**: The top-level container for a diagram, consisting of nodes and edges.
- **Node**: A visual element on the canvas representing a step in a workflow. Key attributes: type, position, size, label, style, bound data (for parameter/module nodes).
- **Edge**: A visual connection between two nodes representing the flow direction. Key attributes: source node, target node, source port, target port, label, style.
- **Port**: A connection point on a node where edges can be attached. Key attributes: type (input/output), position, style.
- **Plugin**: An extension that adds custom functionality to the flowchart editor. Key attributes: name, version, registered node types, registered tools.

### X6 Feature Coverage Mapping

The following table maps X6's documented features to the requirements above:

| X6 Category | X6 Feature | Requirement | Status |
|-------------|-----------|-------------|--------|
| **Basic** | Graph (画布) | FR-001 | Required |
| **Basic** | Node (节点) | FR-002, FR-004 | Required |
| **Basic** | Edge (边) | FR-003 | Required |
| **Basic** | Port (连接桩) | FR-005 | Required |
| **Basic** | Interacting (交互) | FR-006, FR-007, FR-008 | Required |
| **Basic** | Events (事件) | FR-041 | Required |
| **Basic** | Serialization (数据) | FR-010 | Required |
| **Basic** | Animation (动画) | FR-011 | Required |
| **Plugin** | Transform (图形变换) | FR-012 | Required |
| **Plugin** | Snapline (对齐线) | FR-013 | Required |
| **Plugin** | Clipboard (复制粘贴) | FR-014 | Required |
| **Plugin** | Keyboard (快捷键) | FR-015 | Required |
| **Plugin** | History (撤销重做) | FR-016 | Required |
| **Plugin** | Selection (框选) | FR-017 | Required |
| **Plugin** | Scroller (滚动画布) | FR-018 | Required |
| **Plugin** | MiniMap (小地图) | FR-019 | Required |
| **Plugin** | Dnd (拖拽) | FR-020 | Required |
| **Plugin** | Stencil (模板) | FR-021 | Required |
| **Plugin** | Export (导出) | FR-038, FR-039 | Required |
| **Advanced** | Connection Point (连接点) | FR-023 | Required |
| **Advanced** | Tools (工具) | FR-024 | Required |
| **Advanced** | Group (群组) | FR-025 | Required |
| **Advanced** | React/Vue/Angular/HTML Node | FR-026 | Required |
| **Advanced** | Custom Edge/Arrow | FR-027 | Required |
| **Advanced** | Custom Shape/Style | FR-028 | Required |
| **Advanced** | Custom Router/Connector | FR-029 | Required |
| **Advanced** | Custom Highlighter | FR-030 | Required |
| **Advanced** | Custom Port Layout | FR-031 | Required |
| **Advanced** | Custom Tool | FR-032 | Required |
| **Binding** | Parameter Binding | FR-033, FR-036 | Required (Retain) |
| **Binding** | Module Node Binding | FR-034, FR-035 | Required (Retain) |
| **Binding** | Traceability Badge | FR-037 | Required (Retain) |

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a complete flowchart with at least 20 nodes and 30 edges in under 5 minutes.
- **SC-002**: The auto-layout feature can arrange a flowchart with 50 nodes in under 2 seconds.
- **SC-003**: Parameter and module node bindings are persisted with 100% accuracy across save/load cycles.
- **SC-004**: The flowchart editor maintains a frame rate of at least 30 FPS during pan, zoom, and node dragging operations.
- **SC-005**: Users can successfully import and export flowcharts with 100% data fidelity (no loss of node properties, edge connections, or bindings).
- **SC-006**: The plugin architecture allows for the integration of a new custom node type with less than 50 lines of configuration code.
- **SC-007**: All X6 basic features (Graph, Node, Edge, Port, Interacting, Events, Serialization, Animation) are fully functional.
- **SC-008**: All X6 plugins (Transform, Snapline, Clipboard, Keyboard, History, Selection, Scroller, MiniMap, Dnd, Stencil, Export) are integrated and working.
- **SC-009**: All X6 advanced features (Connection Point, Tools, Group, React/Vue/Angular/HTML Node, Custom Edge/Arrow, Custom Shape/Style, Custom Router/Connector, Custom Highlighter, Custom Port Layout, Custom Tool) are supported.
- **SC-010**: Existing parameter binding, module node binding, and traceability features are preserved and functional after the rebuild.
- **SC-011**: The system handles duplicate connection attempts according to `allowMulti` rules without crashing.
- **SC-012**: Deleting a node with connected edges automatically removes all associated edges.
- **SC-013**: Invalid JSON imports fail gracefully with clear error messages, importing valid portions where possible.
- **SC-014**: Zoom is constrained between 10% and 500%, with labels hidden at extreme zoom levels to maintain readability.
- **SC-015**: Large flowcharts (500+ nodes) maintain at least 30 FPS during pan/zoom via virtual rendering.
- **SC-016**: Nodes with bound data (parameter/module binding) trigger a confirmation prompt before deletion.

## Clarifications

### Session 2026-07-10

- **Q1**: Should the system allow multiple edges between the same pair of nodes? → **A**: No, by default `allowMulti` is set to false. Duplicate connections are blocked with visual feedback.
- **Q2**: What happens when a user deletes a node with connected edges? → **A**: All connected edges are automatically removed. Nodes with bound data trigger a confirmation prompt.
- **Q3**: How should invalid JSON imports be handled? → **A**: Invalid data is rejected with clear error messages. Valid portions are imported; invalid portions are skipped with a log.
- **Q4**: What are the zoom constraints? → **A**: Zoom is constrained between 10% and 500%. Labels are hidden at extreme zoom levels.
- **Q5**: How should large flowcharts (500+ nodes) be handled? → **A**: Virtual rendering is used to maintain at least 30 FPS. A performance warning is shown for very large diagrams.

### Session 2026-07-10 (Clarification Round 2)

- **Q6**: How should the implementation be phased given the large scope (FR-001~FR-041)? → **A**: Sequential: Basic → Plugin → Advanced → Binding. Implement each category fully before moving to the next.
  - **Impact on Functional Requirements**: Requirements are already grouped by category (Basic/Plugin/Advanced/Binding). This clarification confirms the implementation order should follow: Basic (FR-001~FR-011) → Plugin (FR-012~FR-022) → Advanced (FR-023~FR-032) → Binding (FR-033~FR-041). Each phase must be independently testable before proceeding.
  - **Impact on Success Criteria**: SC-007 (Basic), SC-008 (Plugin), SC-009 (Advanced), and SC-010 (Binding) align with this phasing and should be validated at the end of each respective phase.
- **Q7**: How should binding data be stored and persisted? → **A**: Embedded in node data properties. Bindings are stored as properties directly on the node object (e.g., `node.data.binding = { entityType, entityId }`).
  - **Impact on Data Model**: Node entity now includes a `binding` field within its `data` property. The binding object has the following schema: `{ entityType: 'PRD' | 'module' | 'feature' | 'parameter', entityId: string, displayLabel?: string }`. This is persisted as part of the node's data in `toJSON()` / `fromJSON()` operations.
  - **Impact on Functional Requirements**: FR-033~FR-037 are clarified to use the embedded approach. Traceability badges (FR-037) read from `node.data.binding` to determine badge visibility and content.
- **Q8**: Which frameworks should be supported for custom node rendering (FR-026)? → **A**: Defer to future phase. Custom framework node rendering (React, Vue, Angular) is out of scope for this rebuild. Only built-in X6 node types (rect, circle, ellipse, polygon, image) and HTML nodes are supported in this phase.
  - **Impact on Functional Requirements**: FR-026 is modified to: "The system MUST support custom node rendering using built-in shapes (rect, circle, ellipse, polygon, image) and HTML content. Framework-specific rendering (React, Vue, Angular) is deferred to a future phase."
  - **Impact on Success Criteria**: SC-009 is adjusted to exclude React/Vue/Angular custom node validation. The advanced feature "Custom Node Rendering" is scoped to HTML nodes only for this phase.
- **Q9**: Should plugins be built-in or dynamically loadable? → **A**: All plugins built-in and always enabled. The 11 plugins (Transform, Snapline, Clipboard, Keyboard, History, Selection, Scroller, MiniMap, Dnd, Stencil, Export) are bundled and enabled by default. Users cannot disable individual plugins.
  - **Impact on Functional Requirements**: FR-012~FR-022 are clarified to be always-on features. No plugin configuration UI is required. Plugin registration is handled at initialization time.
  - **Impact on Architecture**: The plugin system does not need to support dynamic loading or configuration. All plugins are registered during Graph initialization. This simplifies the implementation but increases the initial bundle size.
- **Q10**: Should there be permission checks for data binding operations? → **A**: No additional security. Binding operations do not enforce permission checks beyond the existing flowchart editor access control. Any user with access to the flowchart editor can bind to any entity.
  - **Impact on Functional Requirements**: FR-033~FR-035 are clarified to not require additional permission checks. The binding UI will show all available entities without filtering based on user permissions.
  - **Impact on Security**: This is noted as a known limitation. Future phases may add permission checks if required by the product team.

## Assumptions

- The target users are familiar with basic flowchart concepts.
- The flowchart will be used within a web-based application.
- The underlying graph library (X6) provides the core rendering and interaction capabilities.
- Parameter and module binding data is available through existing APIs.
- Modern browser support is sufficient (latest 2 versions of Chrome, Firefox, Safari, Edge).
- Real-time collaboration features (e.g., multi-user editing) are out of scope for this initial rebuild.
- The system will handle edge cases gracefully: duplicate connections are blocked based on `allowMulti` rules, node deletion cascades to connected edges, invalid imports fail with clear errors, and zoom is constrained to maintain usability.
