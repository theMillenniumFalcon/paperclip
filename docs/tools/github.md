# GitHub tool

Code: `paperclip/tools/github.py`

Read-only GitHub through the **`gh` CLI** (must be installed and `gh auth login`). The model never gets a shell; it picks a command from a fixed allowlist, and this module builds the argv.

## Allowlist

| `command` | `gh` argv | Extra |
| --- | --- | --- |
| `pr list` | `gh pr list` | `--limit` (1–50, default 10), `--json` number/title/author/updatedAt/url |
| `pr view` | `gh pr view <n>` | needs a positive `number` |
| `pr diff` | `gh pr diff <n>` | needs a positive `number` |
| `issue list` | `gh issue list` | same limit + json as PR list |
| `issue view` | `gh issue view <n>` | needs a positive `number` |

Anything else returns a refusal: no merge, comment, close, edit, or push.

Optional `repo` must match `owner/name` and must not start with `-` (so it cannot be parsed as a `gh` flag). Empty `repo` means whatever `gh` considers the current repo.

## Runtime

- 20s timeout. Missing `gh`, timeout, and auth errors get short how-to messages.
- List results are formatted as `#N title — @login (updated YYYY-MM-DD)`. Empty → `(none open)`.
- View/diff output is truncated at 8000 characters with a hint to run `gh` locally for the rest.

`list_prs` / `list_issues` return `(ok, rows_or_error)` for non-tool callers. The model tool is `make_tool(default_repo="")` → `github_read`; omitted `repo` falls back to `default_repo`.
