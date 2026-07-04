# Backend Development Guidelines

> Best practices for backend development in this project — extracted from actual code patterns.

---

## Overview

The backend is a **FastAPI + SQLAlchemy async** application. The PM module follows the same patterns as the core OpenWebUI routers (chats, users, configs, etc.). All guidelines below are backed by real code examples, not aspirational ideals.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Module organization and file layout | ✅ Documented |
| [Database Guidelines](./database-guidelines.md) | ORM patterns, queries, migrations | ✅ Documented |
| [Error Handling](./error-handling.md) | HTTP errors, validation, client responses | ✅ Documented |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, test patterns | ✅ Documented |
| [Logging Guidelines](./logging-guidelines.md) | Structured logging, log levels | ✅ Documented |
| [Flow Engine](./flow-engine.md) | Cross-module flow orchestration, AI-powered content generation | ✅ Documented |

---

## How These Were Created

Each guideline was extracted by inspecting the actual codebase — `routers/pm.py`, `routers/chats.py`, `models/pm.py`, `internal/db.py`, and `backend/tests/`. No aspirational patterns are included; only patterns with existing code examples.

---

**Language**: All documentation should be written in **English**.
