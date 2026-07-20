# Quickstart: Agent Workflow Designer & Architecture Fix

**Feature**: specs/007-agent-workflow-designer
**Date**: 2026-07-11

## Prerequisites

- Open WebUI development environment running
- PM workspace module enabled
- At least one PM project created

## Validation Scenarios

### Scenario 1: Create and Execute a Simple Workflow

**Goal**: Verify the visual workflow designer can create, save, and execute a workflow.

**Steps**:
1. Navigate to **PM Workspace** → **Workflows**
2. Click **New Workflow**
3. Drag a **Start** node onto the canvas
4. Drag an **Agent Call** node onto the canvas
5. Drag an **End** node onto the canvas
6. Connect Start → Agent Call → End
7. Click **Save**
8. Click **Run** with input `{"topic": "Test workflow"}`

**Expected Result**:
- Workflow saves successfully
- Execution completes within 30 seconds
- Output contains agent response

### Scenario 2: Bind Session to Workspace

**Goal**: Verify chat sessions can be bound to PM workspaces.

**Steps**:
1. Open a chat session
2. Click the **Workspace** dropdown in the chat input area
3. Select a PM workspace
4. Ask: "Summarize the requirements in this workspace"

**Expected Result**:
- Session is bound to the selected workspace
- Agent references specific requirements from the workspace
- Response includes citations to workspace documents

### Scenario 3: Agent Cross-Module Operation

**Goal**: Verify agent can read from one module and write to another.

**Steps**:
1. Ensure workspace has requirements and test case modules
2. Ask: "Generate test cases from the requirements"
3. When confirmation modal appears, click **Confirm**

**Expected Result**:
- Agent reads all requirements
- Generates test cases
- Creates entries in the test case module
- Traceability links are created between requirements and test cases

### Scenario 4: Architecture Diagram Display

**Goal**: Verify the architecture diagram displays and is interactive.

**Steps**:
1. Navigate to **PM Workspace** → **Architecture**
2. Wait for diagram to load
3. Click on a module node
4. Hover over a connection

**Expected Result**:
- All module nodes display without errors
- Clicking a node shows details panel
- Hovering over connection shows data flow description

## Test Commands

### API Test (curl)

```bash
# Create workflow
curl -X POST http://localhost:8080/api/pm/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Workflow",
    "project_id": "your-project-uuid",
    "nodes": [...],
    "edges": [...]
  }'

# Execute workflow
curl -X POST http://localhost:8080/api/pm/workflows/{id}/execute \
  -H "Content-Type: application/json" \
  -d '{"input_data": {"topic": "Test"}}'

# Check execution status
curl http://localhost:8080/api/pm/workflows/{id}/executions/{exec_id}
```

### Frontend Test (Manual)

1. Open browser DevTools → Network tab
2. Perform workflow operations
3. Verify API calls return 200/201
4. Check response payloads match contract definitions

## Troubleshooting

### Workflow execution fails
- Check server logs for execution errors
- Verify all nodes have valid configurations
- Ensure skill IDs are registered in the skill registry

### Session binding not working
- Verify workspace exists and has data
- Check session ID is valid
- Ensure user has read permissions on the workspace

### Architecture diagram not loading
- Check browser console for JavaScript errors
- Verify API returns valid node/connection data
- Clear browser cache and retry
