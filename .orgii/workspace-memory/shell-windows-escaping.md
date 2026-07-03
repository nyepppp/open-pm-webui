---
name: Shell command escaping issue on Windows
description: The shell tool on Windows mangles commands containing double-quoted strings with semicolons, causing syntax errors in Python one-liners.
type: feedback
---

When running `python -c "import uuid; print(...)"` on Windows via the shell tool, the command gets mangled and produces `SyntaxError: unterminated string literal`. This happens because the shell tool's command parsing breaks on the semicolon inside double quotes.

**Why:** The shell tool's command-line parsing on Windows does not properly handle double-quoted strings containing semicolons, causing the command to be split incorrectly before reaching the Python interpreter. This has caused the agent to get stuck in infinite retry loops (>30 attempts) without making progress on actual implementation tasks.

**How to apply:** On Windows, avoid using `python -c "...; ..."` with double quotes. Use single quotes for the Python command, or write a temporary script file, or use `python -c` with `%` newline separators, or use `node -e` for quick UUID generation. Alternatively, use `python -c "import uuid" -c "print(uuid.uuid4().hex[:12])"` or just hardcode a UUID manually when needed. **Critical: When stuck in a loop on this issue, STOP immediately and use an alternative approach (hardcode UUID, use node, or write a script file) rather than retrying the same failing command.**
