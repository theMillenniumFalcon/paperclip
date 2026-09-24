# Deterministic eval: GitHub tool

Code: `evals/deterministic/test_gh_tool.py`  
Tool under test: `paperclip/tools/github.py` — see [GitHub tool](../../tools/github.md).

**Offline.** No real `gh`, no GitHub credentials. CI cannot prove “reading works”; these tests pin what would hurt if it broke: **writes never run**, and failures are **strings**, not exceptions.

Design rule: **argv is constructed, never filtered.** The model picks one of five labels; everything else is literals or regex-checked values. Refusal must happen **before** `subprocess.run` — merging after spawn would already have merged.

## Fixtures

| Fixture | Effect |
| --- | --- |
| `no_subprocess` | `subprocess.run` raises `Boom` — any spawn fails the test |
| `capture` | Records `argv` / `kwargs`, returns fake stdout (default `[]`) |

## What the tests check

**Boundary**

- Parametrized write-ish commands (`pr merge`, `gh api`, `auth token`, …) → “read-only” refusal, names allowed commands; must not spawn.
- Allowlist is exactly `pr list`, `pr view`, `pr diff`, `issue list`, `issue view`; argv fragments contain no merge/close/create verbs.
- Bad `repo` values → “not a valid repo”, no subprocess.
- `pr view` / `pr diff` / `issue view` need a positive integer `number`.

**Argv**

- `pr view` → `["gh","pr","view","42","--repo",owner/name]`.
- List commands request `--json`, clamp `--limit` to 50, treat `limit=0` as default 10.
- No `shell=True` in source (AST scan ignores docstrings/comments).
- Timeout is passed through to `subprocess.run`.

**Failures**

- Missing `gh`, timeout → sentence in output, no raise.
- Auth error stderr → mentions `gh auth login`.
- Huge diff stdout → truncated with “truncated”.
- `list_prs` returns parsed rows; `gh_read("pr list")` formats consistently.
- Non-JSON list output → `(False, "not JSON"…)`.

**Registration**

- `make_paperclip(..., gh_tool=False)` → no `github_read`; `gh_tool=True` → registered.
- Tool `description` says read-only and names forbidden verbs.
