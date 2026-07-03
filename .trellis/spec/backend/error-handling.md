# Error Handling

> HTTP errors, validation, and client response patterns — extracted from `routers/pm.py` and `routers/chats.py`.

---

## HTTP Exception Pattern

Use `HTTPException` with `status` module constants. Always include a detail message.

```python
from fastapi import HTTPException, status

# Not found
raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')

# Forbidden (ownership check)
raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')

# Server error (operation failed)
raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to create project')
```

---

## Auth Check Pattern

**Simple auth** — all PM endpoints require `user=Depends(get_verified_user)`:

```python
@router.get('/projects')
async def get_projects(
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    ...
```

**Ownership check** — verify `project.user_id == user.id` before update/delete:

```python
@router.post('/entries/{entry_id}')
async def update_entry(entry_id: str, form_data: PMEntryUpdateForm, user=Depends(get_verified_user), db=...):
    entry = await PMEntries.get_entry_by_id(entry_id, db=db)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Entry not found')
    project = await PMProjects.get_project_by_id(entry.project_id, db=db)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Access denied')
    ...
```

**Admin-only** — use `Depends(get_admin_user)` instead (see `routers/chats.py`).

---

## Graceful Degradation Pattern

Non-critical operations should not fail the main request:

```python
# Auto-create entity for traceability — don't fail entry creation if this fails
try:
    from open_webui.models.pm import PMEntities, PMEntityForm
    entity_form = PMEntityForm(...)
    await PMEntities.insert_new_entity(user.id, entity_form, db=db)
except Exception as e:
    log.warning(f'Failed to auto-create entity for entry {entry.id}: {e}')

# Auto-create initial entry version — same pattern
try:
    from open_webui.models.pm import PMEntryVersions, PMEntryVersionForm
    version_form = PMEntryVersionForm(
        entry_id=entry.id,
        project_id=project_id,
        module_type=form_data.module_type,
        version_number='v1',
        content=entry.content,
        entry_metadata=form_data.data,
        change_summary='Initial version',
    )
    await PMEntryVersions.insert_new_version(user.id, version_form, db=db)
except Exception as e:
    log.warning(f'Failed to auto-create entry version for entry {entry.id}: {e}')
```

**Key**: Use the module-level `log = logging.getLogger(__name__)` (defined at router file top), not `logging.getLogger(__name__)` inside the except block.

---

## Frontend Error Handling

The frontend has two error handling styles:

**Style 1 — Detailed error extraction** (used in entry CRUD):

```typescript
if (!response.ok) {
    let detail = '';
    try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
    throw new Error(`获取条目失败 (${response.status})${detail ? ': ' + detail : ''}`);
}
```

**Style 2 — Simple error** (used in non-critical endpoints):

```typescript
if (!response.ok) throw new Error('Failed to fetch projects');
```

**Convention**: Use Style 1 for user-facing CRUD operations (entries, projects). Use Style 2 for secondary endpoints (entities, relations, agent tools).

---

## Validation

- **Backend**: Pydantic `BaseModel` validates request bodies automatically via FastAPI.
- **Frontend**: `PMFormEditor.svelte` has manual validation with `required` and `validation` fields from `FieldConfig`:

```typescript
interface FieldConfig {
    name: string;
    label: string;
    type: 'text' | 'textarea' | 'select' | 'date' | 'number' | 'combobox' | 'multiselect';
    required?: boolean;
    options?: string[];
    validation?: { min?: number; max?: number; pattern?: string };
}
```

---

## Common Mistakes

1. **Missing ownership check** — Always verify `project.user_id == user.id` before modifying entries.
2. **Catching and swallowing exceptions silently** — Always log at minimum `warning` level.
3. **Using generic error messages** — Include context: `'Entry not found'` not `'Not found'`.
4. **Not handling `response.json()` parse failure** — Wrap in try/catch when extracting error detail.
