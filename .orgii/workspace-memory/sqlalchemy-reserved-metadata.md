---
name: SQLAlchemy metadata reserved field conflict
id: sqlalchemy-reserved-metadata
description: Never use `metadata` as a Column name on SQLAlchemy Base-inheriting classes — it shadows SQLAlchemy's internal metadata attribute and prevents the server from starting.
type: feedback
---

**Rule:** Never name a SQLAlchemy Column `metadata` on any class that inherits from `Base`. The attribute name shadows SQLAlchemy's internal `metadata` property on the class, which causes an `AttributeError` at import time and prevents the backend from starting.

**Why:** SQLAlchemy uses `metadata` internally (e.g., `Base.metadata`). When a model defines `metadata = Column(...)`, the class attribute shadows this, breaking SQLAlchemy's internal machinery. The server fails to start with an opaque AttributeError.

**How to apply:**
- For `PMEntryVersion`, rename `metadata` → `entry_metadata` (the column stores per-version metadata JSON).
- For `PMEntity`, rename `metadata` → `entity_metadata` (the column stores per-entity metadata JSON).
- Also update the corresponding Pydantic model fields (`PMEntryVersionModel`, `PMEntryVersionForm`, `PMEntityModel`, `PMEntityForm`) and all Table Class assignment sites (e.g., `metadata=form_data.metadata` → `entry_metadata=form_data.entry_metadata`).
- This applies to any future table that needs a JSON metadata column: always use a prefixed name like `entry_metadata`, `entity_metadata`, `vmetadata`, or `info` instead of bare `metadata`.