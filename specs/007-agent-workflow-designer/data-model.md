# Data Model: Agent Workflow Designer & Architecture Fix

**Feature**: specs/007-agent-workflow-designer
**Date**: 2026-07-11

## Entity Relationship Diagram

```
Workflow ||--o{ WorkflowNode : contains
Workflow ||--o{ WorkflowEdge : contains
Workflow ||--o{ WorkflowExecution : has_history

WorkflowNode }o--|| SkillContract : references (optional)
WorkflowEdge }o--|| WorkflowNode : source
WorkflowEdge }o--|| WorkflowNode : target

SessionBinding }o--|| PMWorkspace : binds_to
SessionBinding }o--|| ChatSession : binds

TraceabilityLink }o--|| WorkflowNode : source
TraceabilityLink }o--|| ModuleEntry : target

ArchitectureNode }o--o{ ArchitectureNode : connects
```

## Entities

### Workflow

Represents a visual workflow definition.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-gen | Unique identifier |
| name | String | max 255, required | Human-readable name |
| description | Text | optional | Workflow description |
| project_id | UUID | FK → Project, required | Owning project |
| status | Enum | draft / active / archived | Workflow lifecycle |
| nodes | JSON | required | Array of WorkflowNode definitions |
| edges | JSON | required | Array of WorkflowEdge definitions |
| execution_history | JSON | optional | Array of WorkflowExecution records |
| created_at | Timestamp | auto | Creation time |
| updated_at | Timestamp | auto | Last update time |

### WorkflowNode

Represents a single step in a workflow.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-gen | Unique identifier |
| workflow_id | UUID | FK → Workflow, required | Parent workflow |
| type | Enum | start / end / agent_call / data_transform / condition / loop / parallel_merge / custom | Node type |
| name | String | max 255, required | Display name |
| position_x | Float | required | Canvas X position |
| position_y | Float | required | Canvas Y position |
| config | JSON | optional | Node-specific configuration |
| input_schema | JSON | optional | Expected input shape |
| output_schema | JSON | optional | Expected output shape |
| script | Text | optional | Custom node script (for custom type) |
| skill_id | String | FK → SkillContract.id, optional | Linked skill (for custom nodes) |
| created_at | Timestamp | auto | Creation time |

### WorkflowEdge

Represents data flow between nodes.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-gen | Unique identifier |
| workflow_id | UUID | FK → Workflow, required | Parent workflow |
| source_node_id | UUID | FK → WorkflowNode, required | Source node |
| target_node_id | UUID | FK → WorkflowNode, required | Target node |
| data_mapping_rules | JSON | optional | Field-to-field mapping rules |
| label | String | max 255, optional | Edge label for display |
| created_at | Timestamp | auto | Creation time |

### WorkflowExecution

Represents a single workflow run.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-gen | Unique identifier |
| workflow_id | UUID | FK → Workflow, required | Executed workflow |
| status | Enum | pending / running / completed / failed / cancelled | Execution status |
| input_data | JSON | optional | Initial input data |
| output_data | JSON | optional | Final output data |
| node_states | JSON | optional | Per-node execution state |
| logs | JSON | optional | Execution logs |
| started_at | Timestamp | auto | Start time |
| completed_at | Timestamp | optional | Completion time |
| error_message | Text | optional | Error details if failed |

### SessionBinding

Represents a chat session bound to a PM workspace.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-gen | Unique identifier |
| session_id | UUID | FK → ChatSession, required | Bound chat session |
| workspace_id | UUID | FK → PMWorkspace, required | Bound workspace |
| bound_at | Timestamp | auto | Binding time |
| unbound_at | Timestamp | optional | Unbinding time |
| is_active | Boolean | default true | Whether binding is active |

### SkillContract

Represents a reusable PM capability (already partially implemented per Constitution).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | String | PK, kebab-case | Unique identifier (e.g., "pm-generate-prd") |
| name | String | max 255, required | Human-readable name |
| description | Text | required | Skill description |
| output_contract | JSON | required | JSON Schema for output validation |
| invocation | Enum | explicit / autonomous / both | How skill is invoked |
| requires_confirm | Boolean | default true | Whether write ops need confirmation |
| script | Text | optional | Skill implementation script |
| created_at | Timestamp | auto | Creation time |

### TraceabilityLink

Represents relationships between workflow steps and outputs.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-gen | Unique identifier |
| source_entity_type | Enum | workflow / workflow_node / skill / module_entry | Source type |
| source_entity_id | UUID | required | Source entity ID |
| target_entity_type | Enum | workflow / workflow_node / skill / module_entry | Target type |
| target_entity_id | UUID | required | Target entity ID |
| confidence_score | Float | 0.0-1.0 | Relationship confidence |
| created_at | Timestamp | auto | Creation time |

### ArchitectureNode

Represents a module or skill in the architecture diagram.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | String | PK | Unique identifier |
| type | Enum | module / skill / data_flow | Node type |
| label | String | max 255, required | Display label |
| description | Text | optional | Node description |
| position_x | Float | required | Diagram X position |
| position_y | Float | required | Diagram Y position |
| metadata | JSON | optional | Additional node metadata |

## Validation Rules

### Workflow
- Name must be unique within project
- Must have exactly one `start` node
- Must have at least one `end` node
- No orphaned nodes (all nodes must be reachable from start)

### WorkflowNode
- Custom nodes must have either `script` or `skill_id`
- Position coordinates must be non-negative
- Type must be one of the allowed enum values

### WorkflowEdge
- Source and target nodes must belong to the same workflow
- No duplicate edges between the same node pair
- Data mapping rules must reference valid fields in source/output schemas

### SessionBinding
- Only one active binding per session at a time
- Workspace must exist at binding time

### TraceabilityLink
- Source and target entities must exist
- Confidence score must be between 0.0 and 1.0

## State Transitions

### Workflow Status
```
draft → active → archived
  ↓
active → draft (if no executions)
```

### WorkflowExecution Status
```
pending → running → completed
              ↓
            failed
              ↓
           cancelled
```

## Indexes

- Workflow: project_id, status
- WorkflowNode: workflow_id, type
- WorkflowEdge: workflow_id, source_node_id, target_node_id
- WorkflowExecution: workflow_id, status, started_at
- SessionBinding: session_id, workspace_id, is_active
- TraceabilityLink: source_entity_id, target_entity_id
