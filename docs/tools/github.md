# GitHub

Code: `paperclip/tools/github.py`

Read-only pull requests and issues through the `gh` CLI. Paperclip stores no GitHub token. `gh` keeps its own credentials (system keychain). Nothing is written to `.env` or `{PAPERCLIP_HOME}` for auth.

If `gh` is missing and `repo` is `owner/name`, the same read goes to the public GitHub REST API (`https://api.github.com`) with no token. That covers public pull requests, issues, and diffs. Private repositories, and any call with an empty `repo`, still need `gh` on `PATH`. A failure returns a sentence. It does not raise. A GitHub failure must not abort the chat turn.

## Setup

1. Optional for public `owner/name` reads. Required for private repos and for an empty `repo` (so `gh` can use the current directory). Install the [GitHub CLI](https://cli.github.com/) and run `gh auth login` once on this machine. On Windows: `winget install --id GitHub.cli`. On macOS: `brew install gh`.
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
| `gh` missing, `repo` set | Public API. List rows use the same line format. View is `#<number> <title>`, author, date, URL, then the body. Diff is the raw patch. |
| `gh` missing, `repo` empty | Install hint and `gh auth login`. Windows says `winget install --id GitHub.cli`. macOS says `brew install gh`. Other platforms link `https://cli.github.com/`. |
| Public API HTTP error | Status code, then the install hint (private repos need `gh`) |
| Public issue list | Items that contain a `pull_request` key are dropped, matching `gh issue list` |
| Timeout | 20s. Mentions `status.github.com` |
| stderr contains `auth` or `logged in` | `gh is not authenticated. Run gh auth login.` plus the first 200 characters of stderr |
| Other nonzero exit | First 200 characters of stderr |
| List stdout is not JSON | `gh returned something that was not JSON:` plus a short prefix |

## `list_prs` / `list_issues`

`list_prs(repo="", limit=10)` and `list_issues(...)` return `(True, rows)` or `(False, sentence)`. Rows are the parsed JSON. Callers that need counts use these directly. `github_read` formats the same rows, so a list shown to the model matches the structured result.

## `make_tool(default_repo="")`

Registers `github_read`. `repo` on the call, if non-empty, replaces `default_repo`.
