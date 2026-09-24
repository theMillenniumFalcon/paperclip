# Evals

Code: `evals/`

Tests for Paperclip behavior. **Deterministic** suites mock subprocesses and models so CI needs no `gh`, GitHub login, or API keys.

The package is not installed as an editable wheel yet (setuptools sees multiple top-level folders). Pytest adds the repo root to `PYTHONPATH` via `pyproject.toml` — run from the repo root.

## Run

```bash
uv run pytest evals/deterministic/test_gh_tool.py -q
```

All deterministic tests under `evals/deterministic/`:

```bash
uv run pytest evals/deterministic/ -q
```

## Layout

| Path | Role |
| --- | --- |
| `helpers.py` | Fake LLM client, `make_paperclip`, `HAS_KEY` for live evals |
| `deterministic/test_gh_tool.py` | Offline tests for read-only `github_read` |

## Pages

- [Helpers](helpers.md)
- [GitHub tool (deterministic)](deterministic/gh-tool.md)
