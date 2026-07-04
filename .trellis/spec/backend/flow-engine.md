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

LLM responses are unpredictable — they often wrap JSON in markdown code blocks or add explanatory text. **Never use `json.loads(llm_response)` directly.** Always use the `_extract_json` helper:

```python
def _extract_json(llm_response: str, expect_list: bool = True):
    """Extract JSON from LLM response that may include markdown fences or explanatory text."""
    import re
    if not llm_response:
        return [] if expect_list else {}

    # Fast path: direct parse
    try:
        result = json.loads(llm_response)
        if expect_list and not isinstance(result, list):
            result = [result] if result else []
        return result
    except (json.JSONDecodeError, ValueError):
        pass

    # Regex extraction: pull JSON array or object from the response
    try:
        pattern = r'\[.*\]' if expect_list else r'\{.*\}'
        json_match = re.search(pattern, llm_response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            if expect_list and not isinstance(result, list):
                result = [result] if result else []
            return result
    except (json.JSONDecodeError, ValueError):
        pass

    return [] if expect_list else {}
```

Usage in module-level AI endpoints:

```python
# For endpoints returning arrays (extract-parameters, generate-testcases)
parameters = _extract_json(llm_response, expect_list=True)

# For endpoints returning objects (analyze, check, workflow/next)
analysis = _extract_json(llm_response, expect_list=False)

# For generate endpoint (may return string or JSON)
generated_content = _extract_json(llm_response, expect_list=False)
if not generated_content:
    generated_content = llm_response  # Fallback to raw text
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

### Using `metadata=` instead of `entity_metadata=` in PMEntityForm

`PMEntityForm` uses `entity_metadata=` (not `metadata=`) because `metadata` is reserved by SQLAlchemy. When constructing `PMEntityForm` from a dict, use:

```python
# WRONG — will cause Pydantic ValidationError at runtime
entity_form = PMEntityForm(..., metadata=form_data.get('metadata'))

# CORRECT
entity_form = PMEntityForm(..., entity_metadata=form_data.get('metadata'))
```

### Calling `skill.execute()` on BaseSkill

`BaseSkill` has NO `execute()` method. The skill class hierarchy uses:
- `skill.system_prompt` — for LLM system prompt
- `skill.build_user_message(...)` — for constructing user message with context
- `skill.parse_response(llm_response)` — for parsing LLM output into structured result
- `skill.fallback_response()` — for when LLM is unavailable

To execute a skill, call `_call_llm` then use skill methods:

```python
# WRONG — AttributeError at runtime
result = await skill.execute(step.inputs, user, db)

# CORRECT
user_msg = skill.build_user_message(user_message=msg, project_id=pid, ...)
llm_response = await _call_llm(request, user, skill.system_prompt, user_msg)
if llm_response:
    result = skill.parse_response(llm_response)
else:
    result = {'message': skill.fallback_response(), 'actions': None}
```

### Using `eval()` for condition evaluation

`eval()` is a security vulnerability even with `__builtins__` removed. Use `ast.literal_eval()` for safe evaluation of boolean/numeric literals:

```python
# WRONG — security vulnerability
condition_met = eval(step.condition, {"__builtins__": {}}, {})

# CORRECT — safe evaluation of literals only
import ast
condition_met = ast.literal_eval(step.condition)
if not isinstance(condition_met, bool):
    condition_met = bool(condition_met)
```

### DELETE with request body

HTTP DELETE with a request body is non-standard and many clients/proxies will strip the body. Use POST for agent tool endpoints that need a body:

```python
# WRONG — body may be stripped by proxies
@router.delete('/agent/tools/delete_entry')

# CORRECT — reliable body delivery
@router.post('/agent/tools/delete_entry')
```

### Parameter name shadowing builtins

Avoid `format` as a parameter name (shadows Python builtin). Use `export_format` or `output_format` instead.

---

## Break-Loop Analysis: Cross-Layer Contract Bugs

> Deep analysis of the 6 bugs found by trellis-check in `pm-backend-api`. Extracted to prevent recurrence of the entire bug class.

### Root Cause Pattern

**Dominant category: B (Cross-Layer Contract)** — interface mismatches between layers:

| Layer A | Layer B | Mismatch | Bug |
|---------|---------|----------|-----|
| LLM response (markdown-wrapped) | JSON parser (expects raw JSON) | Format contract | `json.loads` fails on markdown fences |
| User dict (`metadata`) | Pydantic model (`entity_metadata`) | Field name contract | 422 ValidationError |
| Workflow code (assumes `execute()`) | BaseSkill class (no `execute()`) | API contract | AttributeError |
| Condition evaluator (`eval`) | Safety requirement | Trust boundary | Security vulnerability |

### _call_llm Empty Model Risk

`_call_llm` uses `'model': ''` — an empty model string. If OpenWebUI has no default model configured, **all LLM-dependent features break silently** (returns empty string, endpoints return fallback "AI 服务暂不可用"). This is a latent bug — not a crash, but every AI feature degrades to empty results with no error message to the user.

**Mitigation**: Consider logging a warning when `_call_llm` receives an empty response, or adding a model configuration check at startup.

### Prevention: When Adding New LLM-Calling Code

Checklist before writing any endpoint that calls `_call_llm`:

- [ ] Use `_extract_json(llm_response, expect_list=...)` — NEVER `json.loads(llm_response)` directly
- [ ] Handle `None`/empty LLM response with a structured fallback
- [ ] Verify the Pydantic model field names match dict keys when constructing forms
- [ ] For new skill integrations, check `BaseSkill` available methods — there is NO `execute()`
- [ ] For agent tool endpoints needing a body, use POST (not DELETE)
- [ ] For condition evaluation, use `ast.literal_eval()` (not `eval()`)
- [ ] Avoid Python builtin names as parameters (`format`, `input`, `list`, `dict`, `type`)
