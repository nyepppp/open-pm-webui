# Directory Structure

> How the backend code is organized — extracted from actual code patterns.

---

## Router Registration

Routers are registered in `backend/open_webui/main.py` with a prefix:

```python
# main.py
app.include_router(pm.router, prefix='/api/v1/pm', tags=['pm'])
```

**Convention**: All PM endpoints are under `/api/v1/pm/...`. The frontend `WEBUI_API_BASE_URL` already includes `/api/v1`, so the client base is `${WEBUI_API_BASE_URL}/pm`.

---

## Module Layout

```
backend/open_webui/
├── main.py                    # App entry, router registration
├── routers/
│   └── pm.py                  # All PM endpoints in one file
├── models/
│   └── pm.py                  # All PM SQLAlchemy models + Pydantic forms
├── internal/
│   └── db.py                  # Base, get_async_db_context, get_async_session
├── utils/
│   └── auth.py                # get_verified_user, get_admin_user
└── pm/                        # PM-specific business logic
    ├── intent.py              # Intent detection for agent chat
    ├── actions.py             # Action validation
    └── skills/                # Skill implementations
        ├── base.py
        ├── prd_generation.py
        └── requirement_analysis.py
```

**Convention**: One router file per domain (`pm.py`), one model file per domain (`pm.py`). Business logic that doesn't belong in the router goes in a dedicated package (`pm/`).

---

## Router File Structure

Each router file follows this pattern:

```python
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from open_webui.utils.auth import get_verified_user
from open_webui.internal.db import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)
router = APIRouter()

# Section headers
############################
# Resource Name
############################

@router.get('/resource', response_model=list[Model])
async def get_resource(
    user=Depends(get_verified_user),
    db: AsyncSession = Depends(get_async_session),
):
    ...
```

---

## Key Conventions

1. **One file per router** — PM keeps all endpoints in `routers/pm.py` (1345+ lines). If it grows further, split by sub-domain (e.g., `pm_entries.py`, `pm_versions.py`).
2. **Models co-located** — SQLAlchemy `Base` classes and Pydantic form/response models live together in `models/pm.py`.
3. **Business logic in `pm/` package** — Skills, intent detection, and actions are separate from the router.
4. **No `__init__.py` re-exports** — Import directly from the module: `from open_webui.models.pm import PMEntries`.
