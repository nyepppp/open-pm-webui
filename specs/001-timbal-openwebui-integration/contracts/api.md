# API Contract: Timbal-OpenWebUI Integration

**Date**: 2026-07-12
**Version**: 1.0.0

## Base URL

All endpoints are prefixed with `/api/v1/timbal`.

## Authentication

All requests require a valid OpenWebUI session token in the `Authorization` header:

```
Authorization: Bearer <token>
```

## Endpoints

### Workflow Management

#### List Workflows

```
GET /workflows
```

**Response**:
```json
{
  "workflows": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "version": "string",
      "created_at": "datetime",
      "updated_at": "datetime"
    }
  ]
}
```

#### Create Workflow

```
POST /workflows
```

**Request Body**:
```json
{
  "name": "string",
  "description": "string",
  "nodes": [...],
  "edges": [...],
  "config": {}
}
```

**Response**:
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "version": "abc123",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### Get Workflow

```
GET /workflows/{workflowId}
```

**Response**:
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "nodes": [...],
  "edges": [...],
  "config": {},
  "version": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### Update Workflow

```
PUT /workflows/{workflowId}
```

**Request Body**: Same as Create Workflow

**Response**: Updated workflow object

#### Delete Workflow

```
DELETE /workflows/{workflowId}
```

**Response**: `204 No Content`

### Workflow Execution

#### Execute Workflow (Async)

```
POST /workflows/{workflowId}/execute
```

**Request Body**:
```json
{
  "inputs": {},
  "sync": false
}
```

**Response**:
```json
{
  "execution_id": "uuid",
  "status": "pending",
  "started_at": "datetime"
}
```

#### Execute Workflow (Sync)

```
POST /workflows/{workflowId}/execute?sync=true
```

**Request Body**:
```json
{
  "inputs": {}
}
```

**Response**:
```json
{
  "execution_id": "uuid",
  "status": "succeeded",
  "outputs": {},
  "completed_at": "datetime"
}
```

#### Stream Workflow Execution

```
GET /workflows/{workflowId}/stream
```

**Headers**:
```
Accept: text/event-stream
```

**Response**: SSE stream of execution events

```
event: status
data: {"status": "running", "progress": 50}

event: output
data: {"node_id": "...", "output": "..."}

event: complete
data: {"status": "succeeded", "outputs": {}}
```

#### Get Execution Status

```
GET /executions/{executionId}
```

**Response**:
```json
{
  "id": "uuid",
  "workflow_id": "uuid",
  "status": "running",
  "inputs": {},
  "outputs": {},
  "logs": [...],
  "started_at": "datetime",
  "completed_at": "datetime",
  "error_message": "string"
}
```

#### Stop Execution

```
POST /executions/{executionId}/stop
```

**Response**:
```json
{
  "id": "uuid",
  "status": "stopped",
  "stopped_at": "datetime"
}
```

### Tool Management

#### List Tools

```
GET /tools
```

**Response**:
```json
{
  "tools": [
    {
      "id": "uuid",
      "name": "string",
      "description": "string",
      "binding_type": "pm_operation|openwebui_skill|openwebui_prompt|openwebui_tool",
      "parameters": {}
    }
  ]
}
```

#### Execute Tool

```
POST /tools/{toolId}/execute
```

**Request Body**:
```json
{
  "parameters": {}
}
```

**Response**:
```json
{
  "success": true,
  "data": {}
}
```

### Configuration

#### Get Configuration

```
GET /config
```

**Response**:
```json
{
  "endpoint_url": "string",
  "timeout": 30,
  "max_concurrent_executions": 10
}
```

#### Update Configuration

```
PUT /config
```

**Request Body**:
```json
{
  "endpoint_url": "string",
  "api_key": "string",
  "timeout": 30,
  "max_concurrent_executions": 10
}
```

**Response**: Updated configuration object

## Error Responses

All errors follow the standard OpenWebUI error format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `TIMBAL_SERVICE_UNAVAILABLE` | Timbal service is unreachable |
| `WORKFLOW_NOT_FOUND` | Workflow ID does not exist |
| `EXECUTION_NOT_FOUND` | Execution ID does not exist |
| `INVALID_WORKFLOW_DEFINITION` | Workflow definition validation failed |
| `TOOL_EXECUTION_FAILED` | Tool execution failed after retries |
| `TIMEOUT_EXCEEDED` | Workflow execution exceeded timeout |

## WebSocket Events

### Connection

```
WS /ws/executions/{executionId}
```

### Events

**Client → Server**:
- `subscribe`: Subscribe to execution updates
- `stop`: Request execution stop

**Server → Client**:
- `status`: Execution status update
- `output`: Node output
- `error`: Error occurred
- `complete`: Execution completed
