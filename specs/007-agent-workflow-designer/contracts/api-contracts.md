# API Contracts: Agent Workflow Designer & Architecture Fix

**Feature**: specs/007-agent-workflow-designer
**Date**: 2026-07-11

## Workflow API

### Create Workflow

```http
POST /api/pm/workflows
```

**Request Body**:
```json
{
  "name": "Idea to PRD Workflow",
  "description": "Transforms an idea into a structured PRD",
  "project_id": "uuid",
  "nodes": [
    {
      "type": "start",
      "name": "Start",
      "position_x": 100,
      "position_y": 100,
      "config": {}
    },
    {
      "type": "agent_call",
      "name": "Brainstorm",
      "position_x": 300,
      "position_y": 100,
      "config": {
        "skill_id": "pm-brainstorm",
        "prompt": "Generate ideas for: {{input.topic}}"
      }
    },
    {
      "type": "data_transform",
      "name": "Format PRD",
      "position_x": 500,
      "position_y": 100,
      "config": {
        "template": "prd_template_v2"
      }
    },
    {
      "type": "end",
      "name": "End",
      "position_x": 700,
      "position_y": 100,
      "config": {}
    }
  ],
  "edges": [
    {
      "source_node_id": "node-1",
      "target_node_id": "node-2",
      "data_mapping_rules": {
        "topic": "input.topic"
      }
    },
    {
      "source_node_id": "node-2",
      "target_node_id": "node-3",
      "data_mapping_rules": {
        "ideas": "output.ideas"
      }
    },
    {
      "source_node_id": "node-3",
      "target_node_id": "node-4",
      "data_mapping_rules": {
        "prd": "output.document"
      }
    }
  ]
}
```

**Response**:
```json
{
  "id": "uuid",
  "name": "Idea to PRD Workflow",
  "status": "draft",
  "nodes": [...],
  "edges": [...],
  "created_at": "2026-07-11T10:00:00Z",
  "updated_at": "2026-07-11T10:00:00Z"
}
```

### Execute Workflow

```http
POST /api/pm/workflows/{workflow_id}/execute
```

**Request Body**:
```json
{
  "input_data": {
    "topic": "AI-powered requirement analysis"
  }
}
```

**Response**:
```json
{
  "execution_id": "uuid",
  "workflow_id": "uuid",
  "status": "running",
  "started_at": "2026-07-11T10:05:00Z"
}
```

### Get Execution Status

```http
GET /api/pm/workflows/{workflow_id}/executions/{execution_id}
```

**Response**:
```json
{
  "id": "uuid",
  "workflow_id": "uuid",
  "status": "completed",
  "input_data": {"topic": "AI-powered requirement analysis"},
  "output_data": {"prd": "..."},
  "node_states": [
    {"node_id": "node-1", "status": "completed", "output": {...}},
    {"node_id": "node-2", "status": "completed", "output": {...}},
    {"node_id": "node-3", "status": "completed", "output": {...}},
    {"node_id": "node-4", "status": "completed", "output": {...}}
  ],
  "started_at": "2026-07-11T10:05:00Z",
  "completed_at": "2026-07-11T10:05:30Z"
}
```

## Session Binding API

### Bind Session to Workspace

```http
POST /api/pm/sessions/{session_id}/bind
```

**Request Body**:
```json
{
  "workspace_id": "uuid"
}
```

**Response**:
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "workspace_id": "uuid",
  "bound_at": "2026-07-11T10:00:00Z",
  "is_active": true
}
```

### Get Session Workspace

```http
GET /api/pm/sessions/{session_id}/workspace
```

**Response**:
```json
{
  "workspace_id": "uuid",
  "name": "My Project",
  "modules": [
    {"id": "uuid", "type": "requirements", "name": "Requirements"},
    {"id": "uuid", "type": "prd", "name": "PRD"}
  ]
}
```

## Skill Invocation API

### Invoke Skill

```http
POST /api/pm/skills/{skill_id}/invoke
```

**Request Body**:
```json
{
  "session_id": "uuid",
  "workspace_id": "uuid",
  "parameters": {
    "topic": "AI-powered requirement analysis"
  }
}
```

**Response**:
```json
{
  "skill_id": "pm-brainstorm",
  "status": "completed",
  "output": {
    "ideas": [...]
  },
  "traceability_links": [
    {"source": "skill-invocation", "target": "module-entry-uuid", "confidence": 0.95}
  ]
}
```

## Architecture Diagram API

### Get Architecture Nodes

```http
GET /api/pm/architecture/nodes
```

**Response**:
```json
{
  "nodes": [
    {
      "id": "module-requirements",
      "type": "module",
      "label": "Requirements",
      "description": "Requirements management module",
      "position": {"x": 100, "y": 100}
    },
    {
      "id": "skill-pm-brainstorm",
      "type": "skill",
      "label": "Brainstorm",
      "description": "Generate ideas from a topic",
      "position": {"x": 300, "y": 100}
    }
  ],
  "connections": [
    {
      "source": "module-requirements",
      "target": "skill-pm-brainstorm",
      "label": "feeds into"
    }
  ]
}
```

## Error Responses

All endpoints return standard error format:

```json
{
  "error": {
    "code": "WORKFLOW_NOT_FOUND",
    "message": "Workflow with id 'uuid' does not exist",
    "details": {}
  }
}
```

Common error codes:
- `WORKFLOW_NOT_FOUND`: Workflow does not exist
- `INVALID_NODE_TYPE`: Node type is not in allowed enum
- `CIRCULAR_DEPENDENCY`: Workflow contains circular node dependencies
- `SESSION_NOT_BOUND`: Session is not bound to any workspace
- `SKILL_NOT_FOUND`: Skill does not exist in registry
- `EXECUTION_FAILED`: Workflow execution failed
