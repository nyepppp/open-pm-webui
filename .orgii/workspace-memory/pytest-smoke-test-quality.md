---
name: pytest smoke tests must actually collect and assert something
description: New pytest files must pass `pytest --collect-only` before being marked done, and assertions must not accept HTTP 500 as a valid outcome.
type: feedback
---

**Rule:** Before declaring a new pytest file complete, run `pytest <path> --collect-only` and confirm every test collects without `fixture 'X' not found` errors. Assertions like `assert response.status_code in [200, 422, 500]` are forbidden — accepting 500 means every server crash counts as a pass.

**Why:** On 2026-07-03, `backend/tests/test_pm_smoke.py` was submitted with 10 test methods requiring `client: TestClient` and `auth_headers: dict` fixtures, but no `conftest.py` existed in `backend/tests/`. `pytest -v` reported 10 ERRORS at setup — every test failed before it ran. Even had the fixtures existed, assertions like `assert response.status_code in [200, 201, 422]` and `in [200, 422, 500]` would treat backend crashes as acceptable, providing zero real coverage. This was reported as "P2 smoke tests完成" but was a placeholder that couldn't detect any regression.

**How to apply:**
- When adding a new test file that requires shared fixtures (`client`, `auth_headers`, `db`, etc.), ensure a `conftest.py` at the appropriate level defines them, or use pytest-fastapi patterns via `TestClient(app)` created inside a fixture.
- Never write `assert response.status_code in [..., 500]` or `in [..., 422]` unless the test is specifically verifying the error path — in that case, also assert on the error body.
- Every smoke test must call `pytest <path> --collect-only` clean and `pytest <path> -v` produce PASSED (not ERROR/SKIPPED) for at least the happy-path case before being considered done.
