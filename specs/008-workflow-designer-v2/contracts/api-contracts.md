# API Contracts: Workflow Designer V2

**Feature**: Workflow Designer V2 - Global Access & AI Integration  
**Date**: 2026-07-11  
**Status**: Draft

---

## Base URL

All endpoints are prefixed with `/api/v1/workflows`.

---

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer <token>
```

---

## Endpoints

### Workflow CRUD

#### List Workflows

```
GET /api/v1/workflows
```

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | integer | No | Page number (default: 1) |
| limit | integer | No | Items per page (default: 20) |
| search | string | No | Search by name or tag |
| status | string | No | Filter by status (draft/active/archived) |
| project_id | UUID | No | Filter by project |

**Response (200)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Content Moderation Pipeline",
      "description": "Moderates content using AI",
      "status": "active",
      "version": 1,
      "owner_id": "uuid",
      "project_ids": ["uuid"],
      "tags": ["moderation", "ai"],
      "created_at": "2026-07-11T00:00:00Z",
      "updated_at": "2026-07-11T00:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 20
}
```

---

#### Get Workflow

```
GET /api/v1/workflows/{workflow_id}
```

**Response (200)**:
```json
{
  "id": "uuid",
  "name": "Content Moderation Pipeline",
  "description": "Moderates content using AI",
  "status": "active",
  "version": 1,
  "owner_id": "uuid",
  "project_ids": ["uuid"],
  "tags": ["moderation", "ai"],
  "nodes": [...],
  "edges": [...],
  "created_at": "2026-07-11T00:00:00Z",
  "updated_at": "2026-07-11T00:00:00Z"
}
```

---

#### Create Workflow

```
POST /api/v1/workflows
```

**Request Body**:
```json
{
  "name": "Content Moderation Pipeline",
  "description": "Moderates content using AI",
  "project_ids": ["uuid"],
  "tags": ["moderation", "ai"],
  "nodes": [
    {
      "type": "start",
      "position": {"x": 100, "y": 100},
      "config": {}
    },
    {
      "type": "llm_call",
      "position": {"x": 300, "y": 100},
      "config": {
        "parameters": [
          {
            "name": "model",
            "type": "select",
            "value": "gpt-4",
            "options": ["gpt-4", "gpt-3.5"]
          }
        ]
      }
    },
    {
      "type": "end",
      "position": {"x": 500, "y": 100},
      "config": {}
    }
  ],
  "edges": [
    {
      "source_node_id": "node_1",
      "target_node_id": "node_2",
      "data_mapping": {}
    }
  ]
}
```

**Response (201)**:
```json
{
  "id": "uuid",
  "name": "Content Moderation Pipeline",
  "status": "draft",
  "version": 1,
  "created_at": "2026-07-11T00:00:00Z"
}
```

---

#### Update Workflow

```
PUT /api/v1/workflows/{workflow_id}
```

**Request Body**: Same as Create Workflow

**Response (200)**:
```json
{
  "id": "uuid",
  "name": "Updated Name",
  "status": "draft",
  "version": 2,
  "updated_at": "2026-07-11T00:00:00Z"
}
```

---

#### Delete Workflow

```
DELETE /api/v1/workflows/{workflow_id}
```

**Response (204)**:
No content.

---

### Workflow Execution

#### Execute Workflow (Async)

```
POST /api/v1/workflows/{workflow_id}/execute
```

**Request Body**:
```json
{
  "input_data": {
    "text": "Content to moderate"
  },
  "triggered_by": "user",
  "session_id": "websocket_session_id"
}
```

**Response (202)**:
```json
{
  "execution_id": "uuid",
  "status": "running",
  "started_at": "2026-07-11T00:00:00Z"
}
```

---

#### Get Execution Status

```
GET /api/v1/workflows/{workflow_id}/executions/{execution_id}
```

**Response (200)**:
```json
{
  "id": "uuid",
  "workflow_id": "uuid",
  "status": "completed",
  "input_data": {...},
  "output_data": {
    "result": "approved",
    "confidence": 0.95
  },
  "started_at": "2026-07-11T00:00:00Z",
  "completed_at": "2026-07-11T00:00:05Z",
  "triggered_by": "user"
}
```

---

#### Get Execution Trace

```
GET /api/v1/workflows/{workflow_id}/executions/{execution_id}/trace
```

**Response (200)**:
```json
{
  "execution_id": "uuid",
  "logs": [
    {
      "node_id": "node_1",
      "node_type": "start",
      "status": "completed",
      "input_data": {...},
      "output_data": {...},
      "execution_time": 10,
      "created_at": "2026-07-11T00:00:00Z"
    },
    {
      "node_id": "node_2",
      "node_type": "llm_call",
      "status": "completed",
      "input_data": {...},
      "output_data": {...},
      "execution_time": 4500,
      "created_at": "2026-07-11T00:00:01Z"
    }
  ]
}
```

---

#### Stop Execution

```
POST /api/v1/workflows/{workflow_id}/executions/{execution_id}/stop
```

**Response (200)**:
```json
{
  "execution_id": "uuid",
  "status": "stopped",
  "stopped_at": "2026-07-11T00:00:03Z"
}
```

---

### AI Generation

#### Generate Workflow from Description

```
POST /api/v1/workflows/generate
```

**Request Body**:
```json
{
  "description": "Create a content moderation pipeline",
  "model": "gpt-4" // optional, defaults to user's default model
}
```

**Response (200)**:
```json
{
  "workflow": {
    "name": "Content Moderation Pipeline",
    "description": "AI-generated workflow for content moderation",
    "nodes": [...],
    "edges": [...]
  }
}
```

---

### Import/Export

#### Export Workflow

```
GET /api/v1/workflows/{workflow_id}/export?format={xml|json}
```

**Response (200)**:
- Content-Type: `application/xml` or `application/json`
- Body: Workflow definition in requested format

---

#### Import Workflow

```
POST /api/v1/workflows/import
```

**Request Body**:
```json
{
  "format": "xml",
  "content": "<bpmn:definitions>...</bpmn:definitions>"
}
```

**Response (201)**:
```json
{
  "id": "uuid",
  "name": "Imported Workflow",
  "warnings": [
    "Unsupported element 'complexGateway' skipped"
  ]
}
```

---

### Templates

#### List Templates

```
GET /api/v1/workflows/templates
```

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| category | string | No | Filter by category |
| search | string | No | Search by name |

**Response (200)**:
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Content Moderation",
      "description": "Moderates content using AI",
      "category": "content",
      "usage_count": 150,
      "rating": 4.5
    }
  ]
}
```

---

#### Create Template from Workflow

```
POST /api/v1/workflows/{workflow_id}/template
```

**Request Body**:
```json
{
  "name": "Content Moderation",
  "description": "Moderates content using AI",
  "category": "content"
}
```

**Response (201)**:
```json
{
  "id": "uuid",
  "name": "Content Moderation",
  "category": "content"
}
```

---

## WebSocket Events

### Connection

Connect to WebSocket for real-time execution updates:

```
ws://{host}/ws/workflows/{execution_id}
```

**Headers**:
```
Authorization: Bearer <token>
```

### Events

#### Server → Client

**execution.started**
```json
{
  "event": "execution.started",
  "execution_id": "uuid",
  "workflow_id": "uuid",
  "started_at": "2026-07-11T00:00:00Z"
}
```

**node.running**
```json
{
  "event": "node.running",
  "execution_id": "uuid",
  "node_id": "node_2",
  "node_type": "llm_call",
  "started_at": "2026-07-11T00:00:01Z"
}
```

**node.completed**
```json
{
  "event": "node.completed",
  "execution_id": "uuid",
  "node_id": "node_2",
  "node_type": "llm_call",
  "output_data": {...},
  "execution_time": 4500,
  "completed_at": "2026-07-11T00:00:05Z"
}
```

**node.failed**
```json
{
  "event": "node.failed",
  "execution_id": "uuid",
  "node_id": "node_2",
  "node_type": "llm_call",
  "error_message": "Model timeout after 30s",
  "failed_at": "2026-07-11T00:00:31Z"
}
```

**execution.completed**
```json
{
  "event": "execution.completed",
  "execution_id": "uuid",
  "workflow_id": "uuid",
  "output_data": {...},
  "completed_at": "2026-07-11T00:00:05Z"
}
```

**execution.failed**
```json
{
  "event": "execution.failed",
  "execution_id": "uuid",
  "workflow_id": "uuid",
  "error_message": "Node 'node_2' failed: Model timeout",
  "failed_at": "2026-07-11T00:00:31Z"
}
```

#### Client → Server

**execution.stop**
```json
{
  "event": "execution.stop",
  "execution_id": "uuid"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "WORKFLOW_NOT_FOUND",
    "message": "Workflow with id 'uuid' not found",
    "details": {}
  }
}
```

**Common Error Codes**:

| Code | Status | Description |
|------|--------|-------------|
| WORKFLOW_NOT_FOUND | 404 | Workflow does not exist |
| WORKFLOW_NOT_ACTIVE | 400 | Workflow is not in active status |
| INVALID_NODE_TYPE | 400 | Node type is not valid |
| CIRCULAR_DEPENDENCY | 400 | Workflow contains circular dependencies |
| EXECUTION_NOT_FOUND | 404 | Execution does not exist |
| EXECUTION_ALREADY_STOPPED | 400 | Execution is already stopped |
| UNAUTHORIZED | 403 | User does not have permission |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| GET /workflows | 100/min |
| POST /workflows | 10/min |
| POST /workflows/{id}/execute | 30/min |
| POST /workflows/generate | 10/min |
| WebSocket | 5 concurrent connections |
