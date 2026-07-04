# PM Flow Engine Guidelines

> Cross-module flow orchestration patterns — extracted from `routers/pm.py` flow engine implementation.

---

## Architecture

The flow engine orchestrates data transformation between PM modules (requirement → PRD → parameter → testcase). It uses **DB-direct access** (never HTTP self-calls) and **AI-powered content generation** via `_call_llm`.

```
FLOW_TEMPLATES (hardcoded)  ──→  FLOW_EXECUTORS (dispatch)  ──→  _flow_* functions (DB+LLM)
         │                              │                              │
    GET /flow/templates          POST /flow/execute           _create_entry_with_entity
    POST /flow/templates         POST /flow/preview           _create_derives_relation
                                                               _find_entity_by_entry_id
```

---

## Flow Templates

5 predefined templates with `id`, `name`, `description`, `input_module`, `output_module`, `steps`:

| Template ID | Input → Output | AI Step |
|---|---|---|
| `requirement_to_parameter` | requirement → parameter | Extract parameters via LLM |
| `requirement_to_prd` | requirement → prd | Generate PRD via LLM |
| `prd_to_parameter` | prd → parameter | Extract parameters via LLM |
| `parameter_to_testcase` | parameter → testcase | Generate test cases via LLM |
| `full_chain` | requirement → testcase | Chains all three above |

Custom templates are stored as entries with `module_type="flow_template"`, prefixed `custom_` in listing.

---

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/pm/flow/templates` | List hardcoded + DB custom templates |
| `POST` | `/pm/flow/preview` | Dry-run preview (no writes) |
| `POST` | `/pm/flow/execute` | Execute flow (requires `confirmed=True`) |
| `POST` | `/pm/flow/templates` | Create custom flow template |

---

## Contracts

### POST /pm/flow/preview

```python
class FlowPreviewRequest(BaseModel):
    template_id: str           # e.g. "requirement_to_parameter"
    source_entry_ids: list[str]  # Entry IDs to flow from
    project_id: str
```

Response: `{ template_id, template_name, source_entries, steps, estimated_outputs }`

### POST /pm/flow/execute

```python
class FlowExecuteRequest(BaseModel):
    template_id: str
    source_entry_ids: list[str]
    project_id: str
    confirmed: bool = False    # MUST be True or 400
```

Response: `{ template_id, template_name, source_entry_ids, status, created_entries, created_relations, step_results, error? }`

### POST /pm/flow/templates

```python
class FlowTemplateCreateRequest(BaseModel):
    name: str
    description: str
    input_module: str
    output_module: str
    steps: list[dict]
    project_id: Optional[str] = None  # Required for DB storage
```

---

## Validation & Error Matrix

| Condition | Error |
|---|---|
| `template_id` not in FLOW_TEMPLATES or DB | 404 Not Found |
| `project_id` not found | 404 Not Found |
| `project.user_id != user.id` | 403 Access Denied |
| `confirmed=False` on execute | 400 Bad Request |
| Source entries not found | Flow returns `{error: 'No source entries found'}` |
| LLM fails or returns unparseable JSON | Flow returns empty created_entries |

---

## Pattern: Entry + Entity + Relation Creation

Every flow-created entry MUST go through `_create_entry_with_entity` which:

1. Creates the `PMEntry` via `PMEntries.insert_new_entry`
2. Auto-creates a `PMEntity` for traceability
3. Auto-creates an initial `PMEntryVersion` (v1)
4. Returns the entry object

Then for each source→target pair:

```python
src_entity_id = await _find_entity_by_entry_id(src_entry.id, db)
tgt_entity_id = await _find_entity_by_entry_id(new_entry.id, db)
if src_entity_id and tgt_entity_id:
    await _create_derives_relation(user, project_id, src_entity_id, tgt_entity_id, db)
```

### Don't: HTTP Self-Reference

```python
# BAD — self-referencing HTTP call (fragile, slow, auth issues)
result = await self._request("POST", "/pm/projects/entries", entry_data)
```

### Do: DB-Direct Access

```python
# GOOD — use models directly in the router
entry = await PMEntries.insert_new_entry(user.id, entry_form, db=db)
```

---

## Pattern: LLM Response Parsing

LLM responses are unpredictable. Always use a regex-based JSON extraction pattern:

```python
llm_response = await _call_llm(request, user, system_prompt, user_message)
items = []
if llm_response:
    try:
        import re
        json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)  # For arrays
        if json_match:
            items = json.loads(json_match.group(0))
    except Exception:
        items = []
```

---

## Pattern: Full Chain Execution

`_flow_full_chain` chains sub-flows and passes created entry IDs between steps:

```python
# Step 1: req → PRD
prd_result = await _flow_requirement_to_prd(source_entry_ids, ...)
prd_entry_id = prd_result.get('prd_entry_id')
if not prd_entry_id:
    # Short-circuit remaining steps
    return {step_results: [skipped...]}

# Step 2: PRD → parameters (using created PRD ID)
param_result = await _flow_prd_to_parameter([prd_entry_id], ...)
param_entry_ids = [e.get('id') for e in param_result.get('created_entries', []) if e.get('id')]

# Step 3: parameters → test cases (using created param IDs)
tc_result = await _flow_parameter_to_testcase(param_entry_ids, ...)
```

---

## Tool Wrapper Pattern

The `pm_flow_tool.py` is a thin wrapper that:
1. Delegates to `/pm/flow/*` API endpoints
2. Handles user confirmation via `__event_call__`
3. Accepts comma-separated `source_entry_ids` string (for agent tool compatibility)
4. Parses `steps` from JSON string in `create_template`

---

## Common Mistakes

### Missing PMRelationModel import

`PMRelationModel` is used in `_create_derives_relation` but was not imported at the top of `pm.py`. **Always import all model classes used in your code at the top-level import block.**

### Forgetting confirmed validation

The `FlowExecuteRequest.confirmed` field defaults to `False`. The endpoint MUST check this before executing, or flows can be triggered without user consent.

### Not creating entities for traceability

Each entry created by a flow MUST have a corresponding `PMEntity` and `PMRelation` (derives) back to its source. Without these, the traceability graph breaks and the `validate_traceability` endpoint will report errors.
