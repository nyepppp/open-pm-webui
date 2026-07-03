# Database Guidelines

> Database patterns and conventions — extracted from `models/pm.py`, `internal/db.py`, and Alembic migrations.

---

## ORM & Session

- **ORM**: SQLAlchemy 2.x with `declarative_base` from `open_webui.internal.db`.
- **Session**: Async via `AsyncSession`. Inject with `Depends(get_async_session)`.
- **Pattern**: Model classes define static async methods that accept `db: AsyncSession` and perform queries.

```python
from open_webui.internal.db import Base, get_async_db_context
from sqlalchemy.ext.asyncio import AsyncSession

class PMProject(Base):
    __tablename__ = 'pm_project'
    id = Column(Text, primary_key=True, unique=True)
    # ...

class PMProjects:
    @staticmethod
    async def get_project_by_id(project_id: str, db: AsyncSession) -> Optional[PMProject]:
        result = await db.execute(select(PMProject).where(PMProject.id == project_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def insert_new_project(user_id: str, form_data: PMProjectForm, db: AsyncSession) -> Optional[PMProject]:
        project = PMProject(id=str(uuid.uuid4()), user_id=user_id, ...)
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project
```

---

## Table Naming

- **Convention**: `pm_` prefix for all PM tables: `pm_project`, `pm_entry`, `pm_entry_version`, `pm_entry_branch`, `pm_entry_merge`, `pm_version`, `pm_entity`, `pm_relation`.
- **Primary keys**: `id = Column(Text, primary_key=True, unique=True)` — UUID strings, not auto-increment integers.
- **Timestamps**: `BigInteger` epoch milliseconds (`created_at`, `updated_at`), NOT `DateTime`.

---

## Column Patterns

| Pattern | Convention | Example |
|---------|-----------|---------|
| ID | `Text`, UUID string | `id = Column(Text, primary_key=True)` |
| Foreign key | `Text`, no SQLAlchemy FK constraint | `project_id = Column(Text)` |
| JSON data | `Column(JSON, nullable=True)` | `data = Column(JSON)`, `meta = Column(JSON)` |
| Status | `Text` with default | `status = Column(Text, default='draft')` |
| Timestamps | `BigInteger` epoch ms | `created_at = Column(BigInteger)` |
| Optional fields | `nullable=True` | `description = Column(Text, nullable=True)` |

**Important**: No SQLAlchemy `ForeignKey` constraints are used — references are by convention only (loose coupling).

---

## Pydantic Form/Model Pattern

Each DB model has a companion Pydantic pair:

```python
# Create form — required fields only
class PMProjectForm(BaseModel):
    name: str
    description: Optional[str] = None

# Update form — all optional
class PMProjectUpdateForm(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

# Response model — all fields, use ConfigDict
class PMProjectModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    status: str = 'active'
    meta: Optional[dict] = None
    created_at: int
    updated_at: int
```

---

## Migrations

- **Tool**: Alembic (`backend/open_webui/migrations/`).
- **File naming**: `<revision_id>_<description>.py` (e.g., `f2e3d4c5b6a7_add_pm_tables.py`).
- **Convention**: Each new table set gets its own migration file.

---

## Common Mistakes

1. **Forgetting `await db.commit()`** — Changes won't persist.
2. **Forgetting `await db.refresh(obj)`** — Returned object won't have auto-generated fields.
3. **Using `datetime` instead of `BigInteger`** — All timestamps must be epoch milliseconds.
4. **Adding FK constraints** — This project uses loose coupling; don't add `ForeignKey()` constraints.
5. **Using `metadata` instead of `entry_metadata` on `PMEntryVersionForm`** — The form field is `entry_metadata`, NOT `metadata`. Pydantic silently ignores unknown fields, so passing `metadata=...` will lose data silently.
6. **Using `metadata` instead of `entity_metadata` on `PMEntityForm`** — Same pitfall: the form field is `entity_metadata`.

---

## Computed Response Fields

Some Pydantic response models include fields that are NOT DB columns — they are computed at query time:

```python
class PMEntryModel(BaseModel):
    # ... DB columns ...
    current_version_number: Optional[str] = None  # computed from latest entry version
    branch_name: Optional[str] = None              # computed from latest entry version
```

These fields are populated by post-query enrichment (e.g., looking up the latest `PMEntryVersion` for each entry) or set directly after creation. They are never written to the database.

---

## Singleton Pattern

PM model classes use instance methods (with `self`), then are instantiated as module-level singletons:

```python
class PMEntryVersions:
    async def insert_new_version(self, user_id: str, form_data: PMEntryVersionForm, ...):
        ...

PMEntryVersions = PMEntryVersions()  # module-level singleton
```

Callers use the singleton name without `()`: `PMEntryVersions.insert_new_version(user_id, form_data, db=db)`.
The first positional arg maps to `self` (which is unused since all methods get their own `db` via `get_async_db_context`).
