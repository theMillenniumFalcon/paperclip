"""Read-only GitHub via the gh CLI. See docs/tools/github.md."""

from __future__ import annotations

import json
import re
import subprocess

from paperclip.tools.registry import Tool

_TIMEOUT = 20
_MAX_CHARS = 8000
_REPO_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*/[A-Za-z0-9_][A-Za-z0-9_.-]*$")

_ALLOWED: dict[str, list[str]] = {
    "pr list": ["pr", "list"],
    "pr view": ["pr", "view"],
    "pr diff": ["pr", "diff"],
    "issue list": ["issue", "list"],
    "issue view": ["issue", "view"],
}
_NEEDS_NUMBER = {"pr view", "pr diff", "issue view"}
_IS_LIST = {"pr list", "issue list"}
_JSON_FIELDS = "number,title,author,updatedAt,url"

_REFUSAL = (
    "Paperclip's GitHub tool is read-only. Allowed commands: "
    + ", ".join(sorted(_ALLOWED))
    + ". It cannot merge, comment, close, edit or push — do those yourself."
)


def _run(argv: list[str], timeout: int = _TIMEOUT) -> tuple[bool, str]:
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return False, ("The gh CLI is not installed. Install it (brew install gh) "
                       "and run `gh auth login`.")
    except subprocess.TimeoutExpired:
        return False, (f"gh timed out after {timeout}s — GitHub or the network is slow. "
                       "Try again, or check status.github.com.")
    except OSError as exc:
        return False, f"could not run gh ({exc})"
    if r.returncode != 0:
        err = (r.stderr or "gh failed").strip()[:200]
        if "auth" in err.lower() or "logged in" in err.lower():
            return False, f"gh is not authenticated. Run `gh auth login`. ({err})"
        return False, err
    return True, r.stdout.strip()


def _argv(command: str, number: int, repo: str, limit: int) -> tuple[bool, list[str] | str]:
    if command not in _ALLOWED:
        return False, _REFUSAL
    if repo and not _REPO_RE.match(repo):
        return False, f"'{repo}' is not a valid repo — use the owner/name form, e.g. octocat/Hello-World."
    argv = ["gh", *_ALLOWED[command]]
    if command in _NEEDS_NUMBER:
        try:
            n = int(number)
        except (TypeError, ValueError):
            return False, f"'{command}' needs a PR/issue number."
        if n <= 0:
            return False, f"'{command}' needs a positive PR/issue number."
        argv.append(str(n))
    if repo:
        argv += ["--repo", repo]
    if command in _IS_LIST:
        argv += ["--limit", str(max(1, min(int(limit or 10), 50)))]
        argv += ["--json", _JSON_FIELDS]
    return True, argv


def _rows(command: str, repo: str, limit: int) -> tuple[bool, list[dict] | str]:
    ok, argv = _argv(command, 0, repo, limit)
    if not ok:
        return False, argv  # type: ignore[return-value]
    ok, out = _run(argv)  # type: ignore[arg-type]
    if not ok:
        return False, out
    try:
        return True, json.loads(out or "[]")
    except json.JSONDecodeError:
        return False, f"gh returned something that was not JSON: {out[:200]}"


def _format(rows: list[dict]) -> str:
    if not rows:
        return "(none open)"
    lines = []
    for r in rows:
        who = (r.get("author") or {}).get("login", "?")
        lines.append(f"#{r.get('number')} {r.get('title', '')} — @{who} "
                     f"(updated {(r.get('updatedAt') or '')[:10]})")
    return "\n".join(lines)


def list_prs(repo: str = "", limit: int = 10) -> tuple[bool, list[dict] | str]:
    return _rows("pr list", repo, limit)


def list_issues(repo: str = "", limit: int = 10) -> tuple[bool, list[dict] | str]:
    return _rows("issue list", repo, limit)


def gh_read(command: str, number: int = 0, repo: str = "", limit: int = 10) -> str:
    if command in _IS_LIST:
        ok, res = _rows(command, repo, limit)
        return _format(res) if ok else str(res)  # type: ignore[arg-type]
    ok, argv = _argv(command, number, repo, limit)
    if not ok:
        return str(argv)
    ok, out = _run(argv)  # type: ignore[arg-type]
    if not ok:
        return out
    if len(out) > _MAX_CHARS:
        return out[:_MAX_CHARS] + (
            f"\n\n… truncated at {_MAX_CHARS} chars. Run `gh {command} {number}` "
            "in a terminal to read the rest."
        )
    return out


def make_tool(default_repo: str = "") -> Tool:
    def run(command: str, number: int = 0, repo: str = "", limit: int = 10) -> str:
        return gh_read(command, number, repo or default_repo, limit)

    return Tool(
        name="github_read",
        description=(
            "Read pull requests and issues from GitHub via the gh CLI. "
            "command must be one of: " + ", ".join(sorted(_ALLOWED)) + ". "
            "READ-ONLY — it cannot merge, comment, close, edit or push, and will "
            "refuse if asked to. Use it to review what is open and what changed."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "one of: " + ", ".join(sorted(_ALLOWED))},
                "number": {"type": "integer", "description": "PR/issue number (required for view and diff)"},
                "repo": {"type": "string", "description": "owner/name; omit to use the current repo"},
                "limit": {"type": "integer", "description": "max rows for list commands, default 10"},
            },
            "required": ["command"],
        },
        fn=run,
    )
