# GitHub

Code: `paperclip/tools/github.py`

Read-only pull requests and issues through the `gh` CLI. Paperclip stores no GitHub token. `gh` keeps its own credentials (system keychain). Nothing is written to `.env` or `{PAPERCLIP_HOME}` for auth.

If `gh` is missing or not logged in, the tool returns a sentence. It does not raise. A GitHub failure must not abort the chat turn.

## Setup

1. Install the [GitHub CLI](https://cli.github.com/) and run `gh auth login` once on this machine.
2. Optional: `PAPERCLIP_GITHUB_REPO=owner/name` (`settings.github_repo`). When the model omits `repo`, `github_read` fills this in. An explicit `repo` argument wins. Empty means `gh` uses its current directory.

`github_read` is always registered. No extra env flag.

## Allowlist

The model picks a **label**. The process argv is built from a fixed table plus validated scalars. Model text never becomes a `gh` flag, and `shell=True` is never used. A command outside the table is refused before `subprocess` runs.

| `command` | argv after `gh` | Extra args |
| --- | --- | --- |
| `pr list` | `pr list` | `--limit`, `--json` |
| `pr view` | `pr view <n>` | |
| `pr diff` | `pr diff <n>` | |
| `issue list` | `issue list` | `--limit`, `--json` |
| `issue view` | `issue view <n>` | |

`--repo owner/name` is appended when `repo` is non-empty. List JSON fields are `number,title,author,updatedAt,url`. `gh pr list` / `gh issue list` default to open items.

Refusal text names the five commands and says the tool cannot merge, comment, close, edit, or push. `gh api` is not in the table.

## Arguments

| Arg | Rule |
| --- | --- |
| `command` | Required. Must be a table key |
| `number` | Required for `pr view`, `pr diff`, and `issue view`. Positive integer. `0`, negative, and non-integers are refused before a process starts |
| `repo` | `owner/name`. Each half must start with a letter, digit, or `_`, then letters, digits, `_`, `.`, or `-`. A value like `-x/y` or `owner/repo; rm -rf ~` is refused, not escaped. Empty is allowed |
| `limit` | List commands only. Default 10. `0` and a missing value use that default. Any other value is clamped to 1–50 |

## Output

| Call | Text |
| --- | --- |
| List, rows | `#<number> <title> — @<login> (updated YYYY-MM-DD)`, one per line |
| List, empty | `(none open)` |
| View or diff | `gh` stdout, stripped |
| Diff or view longer than 8000 characters | First 8000 characters, then a line that says it was truncated and to run `gh <command> <number>` locally |
| `gh` missing | Install hint (`brew install gh`) and `gh auth login` |
| Timeout | 20s. Mentions `status.github.com` |
| stderr contains `auth` or `logged in` | `gh is not authenticated. Run gh auth login.` plus the first 200 characters of stderr |
| Other nonzero exit | First 200 characters of stderr |
| List stdout is not JSON | `gh returned something that was not JSON:` plus a short prefix |

## `list_prs` / `list_issues`

`list_prs(repo="", limit=10)` and `list_issues(...)` return `(True, rows)` or `(False, sentence)`. Rows are the parsed JSON. Callers that need counts use these directly. `github_read` formats the same rows, so a list shown to the model matches the structured result.

## `make_tool(default_repo="")`

Registers `github_read`. `repo` on the call, if non-empty, replaces `default_repo`.
