# Logging Guidelines

> Structured logging patterns — extracted from `routers/pm.py` and `routers/chats.py`.

---

## Logger Setup

Use Python's stdlib `logging` module. Create one logger per module:

```python
import logging
log = logging.getLogger(__name__)
```

---

## Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| `log.error()` | Operation failure that affects the request | `log.error(f'LLM call failed: {e}')` |
| `log.warning()` | Non-critical failure, graceful degradation | `log.warning(f'Failed to auto-create entity for entry {entry.id}: {e}')` |
| `log.info()` | Significant state changes (rarely used in PM) | — |
| `log.debug()` | Verbose diagnostic info (not used currently) | — |

---

## Formatting Conventions

- Use f-strings with descriptive prefixes.
- Include entity IDs for traceability.

```python
# Good
log.error(f'LLM call failed: {e}')
log.warning(f'Failed to auto-create entity for entry {entry.id}: {e}')

# Bad — no context
log.error(str(e))
log.warning('something failed')
```

---

## What to Log

- **LLM call failures** — always at `error` level.
- **Graceful degradation failures** — always at `warning` level.
- **Database operation failures** — logged by the caller after raising `HTTPException`.

---

## What NOT to Log

- **Full request bodies** — may contain user content.
- **Authentication tokens** — never log `user.id` in production unless debugging.
- **Full LLM responses** — may be large; log only failure info.

---

## Common Mistakes

1. **Using `print()` instead of `log`** — Always use the logger.
2. **Importing logging inside functions** — The PM router has `import logging` inside a try/except block as a one-off; the convention is to import at module level.
3. **Not including the entity ID** — Makes debugging impossible in multi-user scenarios.
