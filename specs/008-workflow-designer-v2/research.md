# Research: Workflow Designer V2

**Feature**: Workflow Designer V2 - Global Access & AI Integration  
**Date**: 2026-07-11  
**Status**: Complete

---

## Research Areas

### 1. Workflow Canvas Library

**Decision**: Use [Svelte Flow](https://svelteflow.dev/) (xyflow for Svelte)

**Rationale**:
- Native Svelte support (matches OpenWebUI's SvelteKit architecture)
- Handles node dragging, edge creation, zoom, pan out of the box
- Custom node types with arbitrary Svelte components
- Used by Dify and other modern workflow tools
- MIT license, actively maintained

**Alternatives considered**:
- React Flow: Requires React wrapper in Svelte app — adds complexity
- Svelvet: Svelte-native but less mature, smaller community
- Custom canvas: Too much effort for standard workflow features

**Key findings**:
- Svelte Flow supports custom node types with `Node` component
- Edges support custom labels and animated flows
- Supports minimap, controls, background grid
- Touch support for mobile/tablet

---

### 2. BPMN Import/Export

**Decision**: Use `xmltodict` for XML parsing, custom mapping for node types

**Rationale**:
- Python standard library + xmltodict is lightweight
- BPMN 2.0 spec is well-documented
- Core elements (start, end, task, gateway, sequenceFlow) map cleanly to our node types

**Node mapping (BPMN → Internal)**:

| BPMN Element | Internal Node Type | Notes |
|--------------|-------------------|-------|
| startEvent | start | Entry point |
| endEvent | end | Exit point |
| task | llm_call / agent_call / data_transform | Default to llm_call, user can change |
| userTask | pm_module | PM-specific task |
| serviceTask | webhook / custom | External service call |
| exclusiveGateway | condition | Branching logic |
| parallelGateway | parallel / merge | Fork/join |
| sequenceFlow | edge | Data flow connection |

**Export strategy**:
- Map internal nodes to closest BPMN equivalent
- Custom parameters stored in `extensionElements`
- Unsupported features logged as warnings

---

### 3. AI Workflow Generation

**Decision**: Use OpenWebUI's existing LLM integration with structured prompt engineering

**Rationale**:
- Reuses existing model configuration (no separate setup)
- User's default model is already configured
- Consistent with OpenWebUI's AI-assisted features

**Prompt strategy**:
```
You are a workflow designer assistant. Generate a workflow based on the user's description.

Available node types:
- start: Workflow entry
- end: Workflow exit
- llm_call: Call LLM with prompt
- agent_call: Call OpenWebUI agent
- data_transform: Transform data
- condition: Branch based on condition
- loop: Iterate over data
- parallel: Run branches in parallel
- merge: Combine parallel results
- webhook: Call external API
- pm_module: Interact with PM module

Output format: JSON with nodes[] and edges[]
Each node: { id, type, position: {x, y}, parameters: [] }
Each edge: { id, source, target, condition? }

User description: {user_input}
```

**Generation flow**:
1. User enters natural language description
2. System sends to LLM with structured prompt
3. LLM returns JSON workflow definition
4. System validates and renders on canvas
5. User edits before saving

---

### 4. Execution Engine Architecture

**Decision**: Server-side Python execution engine with WebSocket streaming

**Rationale**:
- Server-side execution ensures data security (API keys, model access)
- WebSocket provides real-time updates to client
- Reuses OpenWebUI's existing backend infrastructure
- Supports long-running workflows

**Engine components**:

```python
class WorkflowEngine:
    async def execute(workflow_id, input_data, session_id):
        # 1. Load workflow definition
        # 2. Build execution graph
        # 3. Execute nodes in topological order
        # 4. Stream progress via WebSocket
        # 5. Return final output
        
    async def execute_node(node, context):
        # Execute single node based on type
        # Handle LLM calls via OpenWebUI's model API
        # Handle PM module calls via existing PM APIs
        # Handle data transformations
        
    async def stream_progress(session_id, node_id, status, output):
        # Send real-time updates to client
```

**Execution modes**:
- **Designer Test Run**: Execute with test inputs, show full trace
- **Chat Execution**: Execute with chat message as input, stream to chat

---

### 5. Chat Integration

**Decision**: Reuse OpenWebUI's chat infrastructure with workflow-specific components

**Rationale**:
- Chat UI already supports streaming messages
- WebSocket connection already established
- Message rendering system extensible

**Integration points**:

1. **Workflow selector in chat input**:
   - Add workflow button next to model selector
   - Dropdown shows user's workflows
   - Pinned workflows appear as quick-access chips

2. **Execution streaming**:
   - Workflow execution creates a "system message" in chat
   - Each node completion updates the message with progress
   - Final output rendered as assistant message

3. **Command trigger**:
   - `/workflow-{id}` command triggers workflow
   - Arguments passed as workflow input

**Message format**:
```json
{
  "type": "workflow_execution",
  "workflow_id": "...",
  "status": "running|completed|failed",
  "current_node": "node_id",
  "progress": 0.5,
  "intermediate_outputs": [...],
  "final_output": "..."
}
```

---

### 6. UI Style Alignment

**Decision**: Use OpenWebUI's existing Tailwind CSS design system

**Rationale**:
- Consistent with rest of application
- Dark mode support built-in
- Component library already available

**Key design tokens**:
- Colors: Use `bg-gray-50/100/200/...` for light, `dark:bg-gray-800/900/950` for dark
- Typography: Use existing text sizes (`text-sm`, `text-lg`, etc.)
- Spacing: Use `px-4 py-3` patterns from existing components
- Buttons: Use `bg-blue-600 hover:bg-blue-700` pattern
- Inputs: Use `border-gray-300 dark:border-gray-600` pattern
- Rounded corners: Use `rounded-xl` (consistent with OpenWebUI)

**Components to reuse**:
- Modal: Existing modal component
- Dropdown: Existing dropdown/select
- Button: Existing button styles
- Input: Existing input styles
- Toast: Existing toast/notification system
- Tooltip: Existing tooltip component

---

## Decisions Summary

| Area | Decision | Rationale |
|------|----------|-----------|
| Canvas | Svelte Flow | Native Svelte, feature-rich, maintained |
| BPMN | xmltodict + custom mapping | Lightweight, sufficient for core elements |
| AI Generation | OpenWebUI LLM integration | Reuses existing setup, consistent |
| Execution | Server-side Python + WebSocket | Secure, real-time, scalable |
| Chat Integration | Reuse chat infrastructure | Minimal new code, consistent UX |
| UI Style | OpenWebUI Tailwind tokens | Visual consistency |

---

## Open Questions (Deferred to Planning)

1. **Workflow storage format**: JSONB in PostgreSQL vs. separate table per entity?
2. **Execution state persistence**: In-memory vs. database for long-running workflows?
3. **Custom node registration**: Dynamic loading vs. static registration?
4. **Versioning strategy**: Full snapshot vs. diff-based versioning?

---

## References

- [Svelte Flow Documentation](https://svelteflow.dev/)
- [BPMN 2.0 Specification](https://www.omg.org/spec/BPMN/2.0/)
- [Dify Workflow Design](https://docs.dify.ai/guides/workflow)
- [OpenWebUI Component Library](src/lib/components/)
