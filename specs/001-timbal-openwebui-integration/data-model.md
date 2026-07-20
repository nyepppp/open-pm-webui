# Data Model: Timbal-OpenWebUI Integration

**Date**: 2026-07-12
**Feature**: Timbal-OpenWebUI Integration
**Spec**: [spec.md](spec.md)

## Entity Relationship Diagram

```
TimbalWorkflow ||--o{ TimbalNode : contains
TimbalWorkflow ||--o{ TimbalExecution : executes
TimbalWorkflow }o--|| TimbalConfig : configured_by
TimbalNode }o--|| TimbalTool : uses
TimbalTool }o--|| PluginBridge : registered_via
```

## Entities

### TimbalWorkflow

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | string | Workflow display name |
| description | text | Workflow description |
| nodes | JSON | Array of node definitions |
| edges | JSON | Array of edge definitions |
| config | JSON | Workflow configuration |
| version | string | Current version (commit hash) |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

### TimbalExecution

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| workflow_id | UUID | Foreign key to TimbalWorkflow |
| status | enum | pending, running, succeeded, failed, stopped |
| inputs | JSON | Execution inputs |
| outputs | JSON | Execution outputs |
| logs | JSON | Execution logs |
| started_at | datetime | Start timestamp |
| completed_at | datetime | Completion timestamp |
| error_message | text | Error message if failed |
| stopped_by | UUID | User who stopped the execution |
| timeout_at | datetime | Timeout timestamp |

### TimbalNode

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| workflow_id | UUID | Foreign key to TimbalWorkflow |
| type | string | Node type (e.g., pm_operation, openwebui_skill) |
| config | JSON | Node configuration |
| inputs | JSON | Input mappings |
| outputs | JSON | Output mappings |
| position_x | float | X position on canvas |
| position_y | float | Y position on canvas |

### TimbalTool

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | string | Tool name |
| description | text | Tool description |
| parameters | JSON | Parameter schema |
| return_schema | JSON | Return value schema |
| handler_function | string | Function reference |
| binding_type | enum | pm_operation, openwebui_skill, openwebui_prompt, openwebui_tool |

### TimbalConfig

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| endpoint_url | string | Timbal API endpoint |
| api_key | string | API key for authentication |
| timeout | integer | Request timeout in seconds |
| max_concurrent_executions | integer | Maximum concurrent executions |

## State Machine

### TimbalExecution Status Transitions

```
pending → running: When execution starts
running → succeeded: When workflow completes successfully
running → failed: When workflow encounters an error
running → stopped: When user manually stops the execution
pending → failed: When execution fails to start (e.g., validation error)
running → failed: When execution exceeds timeout_at
```

## Validation Rules

- **TimbalWorkflow**: name must be unique, nodes must form a valid DAG
- **TimbalExecution**: status must be a valid enum value, workflow_id must exist
- **TimbalNode**: type must be a registered node type, position must be non-negative
- **TimbalTool**: name must be unique, parameters must be valid JSON Schema
- **TimbalConfig**: endpoint_url must be a valid URL, timeout must be positive
