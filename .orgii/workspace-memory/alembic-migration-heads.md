---
name: Alembic migrations must chain to current head
description: When adding an Alembic revision, always chain down_revision to the actual current head reported by `alembic heads`, not an arbitrary earlier revision.
type: feedback
---

**Rule:** Before creating a new Alembic migration, run `alembic heads` (or scan `migrations/versions/` for revisions not referenced as any `down_revision`) to find the *true* current head. Set the new revision's `down_revision` to that head. If a rebase creates two heads, resolve with `alembic merge -m "..." <head_a> <head_b>` before shipping.

**Why:** On 2026-07-03, `f2e3d4c5b6a7_add_pm_tables.py` set `down_revision = 'f1e2d3c4b5a6'` (a mid-chain revision — access grant table), while the real head was `461111b60977`. Result: two heads coexist, and `command.upgrade(alembic_cfg, 'head')` raises `alembic.util.exc.CommandError: Multiple head revisions are present`. In this repo the backend still boots because `main.py:675 Base.metadata.create_all` masks the migration failure, but production and any environment that trusts `alembic upgrade` will refuse to start or silently skip migrations.

**Fixed (2026-07-03T01:10Z):** sde-implementer corrected `down_revision` from `'f1e2d3c4b5a6'` to `'461111b60977'` in `f2e3d4c5b6a7_add_pm_tables.py`.

**How to apply:**
- Before writing the revision file: `python -c "from alembic.config import Config; from alembic.script import ScriptDirectory; cfg = Config('backend/open_webui/alembic.ini'); cfg.set_main_option('script_location', 'backend/open_webui/migrations'); print(ScriptDirectory.from_config(cfg).get_heads())"` — or grep `revision` values not referenced as any `down_revision`.
- If a branch already exists, do NOT rewrite history in a shipped revision. Add a merge revision instead: `alembic merge -m "merge <branch> into main" <head_a> <head_b>`.
- After creating a migration, verify with `alembic heads` that there is exactly one head.
