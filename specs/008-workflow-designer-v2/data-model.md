# Data Model: Workflow Designer V2

**Feature**: Workflow Designer V2 - Global Access & AI Integration  
**Date**: 2026-07-11  
**Status**: Draft

---

## Entity Relationship Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Workflow     │────<│  WorkflowNode   │     │  WorkflowEdge   │
│                 │     │                 │     │                 │
│ id (PK)         │     │ id (PK)         │     │ id (PK)         │
│ name            │     │ workflow_id (FK)│     │ workflow_id (FK)│
│ description     │     │ type            │     │ source_node_id  │
│ status          │     │ config          │     │ target_node_id  │
│ version         │     │ position_x      │     │ data_mapping    │
│ owner_id (FK)   │     │ position_y      │     │ created_at      │
│ created_at      │     │ input_schema    │     └─────────────────┘
│ updated_at      │     │ output_schema   │
└─────────────────┘     └─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐     ┌─────────────────┐
│WorkflowExecution│────<│  ExecutionLog   │
│                 │     │                 │
│ id (PK)         │     │ id (PK)         │
│ workflow_id (FK)│     │ execution_id(FK)│
│ status          │     │ node_id         │
│ input_data      │     │ status          │
│ output_data     │     │ input_data      │
│ started_at      │     │ output_data     │
│ completed_at    │     │ execution_time  │
│ triggered_by    │     │ created_at      │
└─────────────────┘     └─────────────────┘

┌─────────────────┐     ┌─────────────────┐
│WorkflowTemplate │     │  WorkflowExport │
│                 │     │                 │
│ id (PK)         │     │ id (PK)         │
│ name            │     │ workflow_id (FK)│
│ description     │     │ format          │
│ workflow_def    │     │ content         │
│ category        │     │ exported_at     │
│ usage_count     │     └─────────────────┘
│ rating          │
└─────────────────┘
```

---

## Entity Definitions

### Workflow

Represents a visual workflow definition.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto | Unique identifier |
| name | VARCHAR(255) | NOT NULL | Workflow name |
| description | TEXT | nullable | Workflow description |
| status | ENUM | DEFAULT 'draft' | draft / active / archived |
| version | INTEGER | DEFAULT 1 | Version number |
| owner_id | UUID | FK → users.id | Creator |
| project_ids | ARRAY<UUID> | nullable | Projects this workflow is available in |
| tags | ARRAY<VARCHAR> | nullable | Searchable tags |
| created_at | TIMESTAMP | auto | Creation time |
| updated_at | TIMESTAMP | auto | Last update time |

### WorkflowNode

Represents a single step in a workflow.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto | Unique identifier |
| workflow_id | UUID | FK → Workflow.id, CASCADE | Parent workflow |
| type | ENUM | NOT NULL | start / end / llm_call / agent_call / data_transform / condition / loop / parallel / merge / webhook / pm_module / custom |
| config | JSONB | NOT NULL | Node-specific configuration |
| position_x | FLOAT | NOT NULL | Canvas X position |
| position_y | FLOAT | NOT NULL | Canvas Y position |
| input_schema | JSONB | nullable | Expected input shape |
| output_schema | JSONB | nullable | Expected output shape |
| created_at | TIMESTAMP | auto | Creation time |

**Node config structure** (JSONB):
```json
{
  "parameters": [
    {
      "id": "param_1",
      "name": "model",
      "type": "select",
      "required": true,
      "default_value": "gpt-4",
      "options": ["gpt-4", "gpt-3.5", "claude"],
      "description": "LLM model to use"
    },
    {
      "id": "param_2",
      "name": "temperature",
      "type": "number",
      "required": false,
      "default_value": 0.7,
      "validation_rules": ["min:0", "max:2"],
      "description": "Temperature for generation"
    }
  ],
  "custom_parameters": [
    {
      "id": "custom_1",
      "name": "custom_header",
      "type": "text",
      "required": false,
      "default_value": "",
      "description": "Custom header for API call"
    }
  ]
}
```

### WorkflowEdge

Represents data flow between nodes.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto | Unique identifier |
| workflow_id | UUID | FK → Workflow.id, CASCADE | Parent workflow |
| source_node_id | UUID | FK → WorkflowNode.id | Source node |
| target_node_id | UUID | FK → WorkflowNode.id | Target node |
| data_mapping | JSONB | nullable | Field mapping rules |
| created_at | TIMESTAMP | auto | Creation time |

**Data mapping structure** (JSONB):
```json
{
  "mappings": [
    {
      "source_field": "output.text",
      "target_field": "input.prompt",
      "transformation": "none" // or "uppercase", "json_parse", etc.
    }
  ]
}
```

### WorkflowExecution

Represents a single workflow run.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto | Unique identifier |
| workflow_id | UUID | FK → Workflow.id | Executed workflow |
| status | ENUM | DEFAULT 'pending' | pending / running / completed / failed / stopped |
| input_data | JSONB | nullable | Input provided to workflow |
| output_data | JSONB | nullable | Final output |
| started_at | TIMESTAMP | nullable | Start time |
| completed_at | TIMESTAMP | nullable | Completion time |
| triggered_by | VARCHAR | NOT NULL | user / chat / api |
| session_id | UUID | nullable | WebSocket session for streaming |
| created_at | TIMESTAMP | auto | Creation time |

### ExecutionLog

Represents execution trace for a single node.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto | Unique identifier |
| execution_id | UUID | FK → WorkflowExecution.id, CASCADE | Parent execution |
| node_id | UUID | FK → WorkflowNode.id | Executed node |
| status | ENUM | NOT NULL | pending / running / completed / failed |
| input_data | JSONB | nullable | Node input |
| output_data | JSONB | nullable | Node output |
| execution_time | INTEGER | nullable | Execution time in ms |
| error_message | TEXT | nullable | Error details if failed |
| created_at | TIMESTAMP | auto | Creation time |

### WorkflowTemplate

Represents a reusable workflow template.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto | Unique identifier |
| name | VARCHAR(255) | NOT NULL | Template name |
| description | TEXT | nullable | Template description |
| workflow_definition | JSONB | NOT NULL | Full workflow JSON |
| category | VARCHAR(100) | NOT NULL | Template category |
| usage_count | INTEGER | DEFAULT 0 | Usage counter |
| rating | FLOAT | DEFAULT 0 | User rating (0-5) |
| created_at | TIMESTAMP | auto | Creation time |
| updated_at | TIMESTAMP | auto | Last update time |

### WorkflowExport

Represents an export/import record.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto | Unique identifier |
| workflow_id | UUID | FK → Workflow.id | Exported workflow |
| format | ENUM | NOT NULL | xml / json |
| content | TEXT | NOT NULL | Exported content |
| exported_at | TIMESTAMP | auto | Export time |

---

## State Transitions

### Workflow Status

```
[draft] ──(publish)──> [active] ──(archive)──> [archived]
   │                        │
   └─(delete)               └─(delete)
```

### WorkflowExecution Status

```
[pending] ──(start)──> [running] ──(complete)──> [completed]
   │                        │
   │                        ├─(fail)─────────> [failed]
   │                        │
   └─(stop)                 └─(stop)────────> [stopped]
```

---

## Indexes

| Table | Columns | Purpose |
|-------|---------|---------|
| Workflow | owner_id | Filter by owner |
| Workflow | status | Filter by status |
| Workflow | project_ids (GIN) | Cross-project queries |
| WorkflowNode | workflow_id | Cascade operations |
| WorkflowEdge | workflow_id | Cascade operations |
| WorkflowEdge | source_node_id | Find outgoing edges |
| WorkflowEdge | target_node_id | Find incoming edges |
| WorkflowExecution | workflow_id | Execution history |
| WorkflowExecution | status | Filter by status |
| ExecutionLog | execution_id | Execution trace |
| ExecutionLog | node_id | Node execution history |
| WorkflowTemplate | category | Filter by category |

---

## Validation Rules

### Workflow
- Name must be unique per owner
- Status transitions must follow state machine
- At least one start node and one end node required for activation

### WorkflowNode
- Type must be valid enum value
- Position must be within canvas bounds (-10000 to +10000)
- Config must match node type schema

### WorkflowEdge
- Source and target nodes must exist in same workflow
- No duplicate edges between same source/target pair
- No self-loops (source == target)
- Source node must have output compatible with target node's input

### WorkflowExecution
- Can only start if workflow status is 'active'
- Input data must match workflow's input schema

---

## Data Volume Estimates

| Entity | Expected Volume | Growth Rate |
|--------|----------------|-------------|
| Workflow | 1,000 per project | Linear with users |
| WorkflowNode | 10-50 per workflow | Fixed per workflow |
| WorkflowEdge | 10-50 per workflow | Fixed per workflow |
| WorkflowExecution | 10,000 per day | Linear with usage |
| ExecutionLog | 100-500 per execution | Fixed per execution |
| WorkflowTemplate | 100 system + user templates | Slow growth |

---

## Migration Strategy

### Phase 1: Create Tables
- Create all tables with foreign key constraints
- Add indexes
- Set up triggers for updated_at

### Phase 2: Migrate Existing Data
- Migrate existing PM workflow data to new schema
- Map old node types to new types
- Validate and fix orphaned records

### Phase 3: Enable Features
- Enable global sidebar entry
- Enable chat integration
- Enable AI generation

---

## Notes

- JSONB used for flexible schema (parameters, config, mappings)
- GIN index on project_ids for efficient cross-project queries
- Execution logs purged after 30 days (configurable)
- Workflow definitions versioned via Workflow.version field
