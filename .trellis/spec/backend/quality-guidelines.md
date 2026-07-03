# Quality Guidelines

> Code quality standards for backend development — extracted from existing test and code patterns.

---

## Test Patterns

Tests live in `backend/tests/`. The current test suite is **smoke tests only**.

### Test Structure

```python
# conftest.py — fixtures
@pytest.fixture
def client():
    from open_webui.main import app
    return TestClient(app)

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token", "Content-Type": "application/json"}

# test_pm_smoke.py — test class
class TestPMEndpoints:
    def test_get_projects(self, client: TestClient, auth_headers: dict):
        response = client.get("/pm/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
```

### Test Conventions

- Use **class-based** grouping (`class TestPMEndpoints`).
- Use **pytest fixtures** for client and auth.
- **Lenient status checks** for dependent tests: `assert response.status_code in [200, 201, 422]`.
- **Skip on dependency failure**: `pytest.skip("Could not create project for entry test")`.

---

## Required Patterns

1. **Async endpoints** — All PM endpoints must be `async def`.
2. **Auth dependency** — All PM endpoints must have `user=Depends(get_verified_user)`.
3. **DB dependency** — All PM endpoints that query the DB must have `db: AsyncSession = Depends(get_async_session)`.
4. **Response model** — Use `response_model=` parameter on GET/list endpoints.
5. **Section headers** — Use `####` comment blocks to separate resource groups.

---

## Forbidden Patterns

1. **`eval()` on user input** — The workflow executor uses `eval(step.condition, {"__builtins__": {}}, {})`. This is a known security risk and should be replaced with a safe expression evaluator.
2. **Synchronous DB calls** — Never use sync SQLAlchemy sessions.
3. **Hardcoded error strings without context** — Always include entity identifiers.
4. **Import inside function body** — Except for lazy/circular import avoidance, import at module level.

---

## Code Review Checklist

- [ ] All new endpoints have `user=Depends(get_verified_user)`
- [ ] Ownership checks on update/delete endpoints
- [ ] Async DB session properly injected
- [ ] Error messages include entity context
- [ ] Non-critical failures use try/except + warning log, not HTTPException
- [ ] Pydantic form models have matching update (all Optional) and response (all fields) variants
- [ ] No `eval()` or `exec()` on user-controlled data
