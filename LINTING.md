# Linting

Two tools are configured. Run them both before committing.

---

## Tools

| Tool | What it checks | Config |
|---|---|---|
| **ruff** | Code quality, unused imports, PEP 8 style, import order | `ruff.toml` |
| **mypy** | Type annotations | `mypy.ini` |

---

## Running

```bash
# Check for lint errors
ruff check .

# Check types
mypy server.py api.py formatting.py views.py context_data.py apply_changes.py
```

Both must pass with zero errors before a change is complete.

---

## What ruff enforces

| Rule set | What it catches |
|---|---|
| `E` (pycodestyle) | PEP 8 style violations — spacing, indentation, blank lines |
| `F` (pyflakes) | Undefined names, unused imports, unused variables |
| `I` (isort) | Import order — stdlib → third-party → local |
| `UP` (pyupgrade) | Outdated Python syntax (e.g. `Optional[X]` → `X \| None`) |

Line length limit is **120 characters**. `views.py` is excluded from the line-length rule because it contains long inline HTML/CSS strings.

---

## What mypy enforces

Type annotations are checked across all six Python modules. Third-party packages without stubs (e.g. `mcp`, `httpx`, `starlette`) are silently accepted via `ignore_missing_imports = True` — only our own code is checked.

---

## Installing

```bash
pip install ruff mypy
```
