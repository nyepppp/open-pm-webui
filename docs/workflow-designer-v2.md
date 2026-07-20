# Workflow Designer V2 - Documentation

## Overview

The Workflow Designer V2 is a visual workflow builder for OpenWebUI that enables users to create, edit, and execute workflows through a drag-and-drop interface.

## Architecture

### Backend Components

#### Workflow Execution Engine (`backend/open_webui/services/workflow/engine.py`)
- **WorkflowExecutionEngine**: Main execution engine
  - Supports topological execution of workflow nodes
  - Handles multiple node types: start, end, agent_call, data_transform, condition, loop, parallel_merge, custom
  - Manages data flow between nodes
  - Supports conditional branching and loops
  - Handles parallel execution
  - Provides error handling and logging
  - Streams execution progress via WebSocket

#### Node Types

| Node Type | Description | Status |
|-----------|-------------|--------|
| start | Workflow entry point | ✅ Implemented |
| end | Workflow exit point | ✅ Implemented |
| agent_call | Calls OpenWebUI LLM/agent | ✅ Implemented (with fallback) |
| data_transform | Transforms data (JSON mapping, filtering, merging) | ✅ Implemented |
| condition | Conditional branching | ✅ Implemented |
| loop | Iterative processing | ✅ Implemented |
| parallel_merge | Parallel execution and result merging | ✅ Implemented |
| custom | Custom script execution | ✅ Implemented |

#### Services

- **ai_generator.py**: AI-assisted workflow generation from natural language
- **bpmn_converter.py**: BPMN 2.0 XML import/export
- **json_converter.py**: JSON import/export
- **chat_execution.py**: Chat integration for workflow execution
- **websocket.py**: Real-time execution streaming
- **conditions.py**: Safe condition expression evaluation

### Frontend Components

#### Workflow Designer (`src/lib/components/workflow-v2/`)
- **WorkflowDesigner.svelte**: Main designer component
- **Canvas.svelte**: Visual canvas for node placement and connection
- **NodeSidebar.svelte**: Draggable node palette
- **PropertyPanel.svelte**: Node configuration panel
- **types.ts**: TypeScript type definitions

#### Chat Integration
- **WorkflowSelector.svelte**: Workflow selection in chat input
- **MessageInput.svelte**: Integrated chat input with workflow support

## API Endpoints

### Workflow CRUD
- `GET /api/workflows` - List all workflows
- `POST /api/workflows` - Create workflow
- `GET /api/workflows/{id}` - Get workflow
- `PUT /api/workflows/{id}` - Update workflow
- `DELETE /api/workflows/{id}` - Delete workflow

### Execution
- `POST /api/workflows/{id}/execute` - Execute workflow
- `GET /api/workflows/executions/{id}` - Get execution status

### Import/Export
- `POST /api/workflows/{id}/export/json` - Export to JSON
- `POST /api/workflows/{id}/export/bpmn` - Export to BPMN/XML
- `POST /api/workflows/import/json` - Import from JSON
- `POST /api/workflows/import/bpmn` - Import from BPMN

## Testing

### Backend Tests
```bash
# Test workflow execution engine
python -m pytest backend/tests/test_v2_workflows.py -xvs

# Test conditions
python -c "from open_webui.services.workflow.conditions import evaluate_condition; print(evaluate_condition('1 > 0', {}))"
```

### Frontend Tests
```bash
# Run Svelte tests
npm run test
```

## Usage

### Creating a Workflow
1. Navigate to `/workflows`
2. Click "新建工作流" (Create Workflow)
3. Enter name and description
4. Drag nodes from sidebar to canvas
5. Connect nodes with edges
6. Configure node properties
7. Save workflow

### Executing a Workflow
1. Open workflow designer
2. Click "执行" (Execute)
3. View execution status and results

### Chat Integration
1. Open chat
2. Click workflow button in input area
3. Select workflow
4. Type message and send
5. Workflow executes with message as input

## Configuration

### Environment Variables
- `WEBUI_SECRET_KEY`: Required for authentication
- `MAX_WORKFLOW_NODES`: Maximum nodes per workflow (default: 100)
- `MAX_EXECUTION_TIME`: Maximum execution time in seconds (default: 300)

## Troubleshooting

### Common Issues
1. **Import errors**: Ensure `backend` is in Python path
2. **Database errors**: Run migrations
3. **WebSocket errors**: Check Socket.IO configuration

## Future Improvements

1. Real LLM integration for agent_call nodes
2. Advanced debugging tools
3. Workflow templates marketplace
4. Collaborative editing
5. Version control for workflows
