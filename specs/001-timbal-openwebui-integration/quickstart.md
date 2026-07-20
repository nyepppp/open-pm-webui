# Quickstart: Timbal-OpenWebUI Integration

**Date**: 2026-07-12
**Feature**: Timbal-OpenWebUI Integration

## Prerequisites

- OpenWebUI is running locally
- Timbal service is accessible via HTTP/HTTPS
- You have admin access to OpenWebUI

## Setup

### 1. Configure Timbal Endpoint

Navigate to **Settings > Timbal Integration** and configure:

- **Endpoint URL**: `http://localhost:3000` (your Timbal service URL)
- **API Key**: Your Timbal API key
- **Timeout**: 30 seconds
- **Max Concurrent Executions**: 10

### 2. Verify Connection

Click **Test Connection** to verify the Timbal service is reachable.

## Validation Scenarios

### Scenario 1: Execute a Simple Workflow

**Goal**: Execute a workflow that fetches the list of projects from the PM workspace.

**Steps**:

1. Navigate to **Workflows > New Workflow**
2. Drag a "PM Data Source" node onto the canvas
3. Configure the node:
   - **Operation**: `get_project_list`
   - **Parameters**: `{}`
4. Connect the node to an "Output" node
5. Click **Save** and name the workflow "List Projects"
6. Click **Execute**
7. Verify the execution status shows "succeeded"
8. Verify the output contains a list of projects

**Expected Result**: Workflow executes successfully and returns a list of projects.

### Scenario 2: Execute Workflow from Chat

**Goal**: Trigger a workflow from the OpenWebUI chat interface.

**Steps**:

1. Open the chat interface
2. Type: `/workflow run "List Projects"`
3. Verify the workflow executes
4. Verify results are displayed in the chat

**Expected Result**: Workflow is triggered and results are streamed to the chat.

### Scenario 3: Create a Workflow with PM Parameter Mapping

**Goal**: Create a workflow that creates a requirement in a specific project.

**Steps**:

1. Navigate to **Workflows > New Workflow**
2. Drag a "PM Data Source" node onto the canvas
3. Configure the node:
   - **Operation**: `create_requirement`
   - **Parameters**:
     ```json
     {
       "project_id": "{{project.id}}",
       "title": "New Requirement",
       "description": "Created via workflow"
     }
     ```
4. Connect the node to an "Output" node
5. Click **Save** and name the workflow "Create Requirement"
6. Click **Execute**
7. Verify the requirement is created in the PM workspace

**Expected Result**: A new requirement is created in the selected project.

### Scenario 4: Test Error Handling

**Goal**: Verify error handling when Timbal service is unavailable.

**Steps**:

1. Stop the Timbal service
2. Navigate to **Workflows**
3. Try to execute any workflow
4. Verify an error message is displayed

**Expected Result**: Clear error message indicating Timbal service is unavailable.

### Scenario 5: Test Version Control

**Goal**: Verify workflow versioning works correctly.

**Steps**:

1. Navigate to **Workflows > New Workflow**
2. Create a simple workflow
3. Click **Save** (version 1)
4. Modify the workflow
5. Click **Save** (version 2)
6. Navigate to **Version History**
7. Verify both versions are listed
8. Roll back to version 1
9. Verify the workflow is restored to version 1

**Expected Result**: Version history is maintained and rollback works correctly.

## Troubleshooting

### Timbal Service Unreachable

- Verify the Timbal endpoint URL is correct
- Check network connectivity to the Timbal service
- Verify the Timbal service is running

### Workflow Execution Fails

- Check the execution logs for error details
- Verify the workflow definition is valid
- Check Timbal service logs for errors

### Tool Execution Fails

- Verify the tool parameters are correct
- Check PM workspace data exists
- Verify the tool binding is configured correctly
