"""Read-only GitHub via the gh CLI, with a public API fallback. See docs/tools/github.md."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request

from paperclip.tools.registry import Tool

_TIMEOUT = 20
_MAX_CHARS = 8000
_API = "https://api.github.com"
_NO_CLI = "\0"
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


def _install_hint() -> str:
    if sys.platform == "win32":
        how = "winget install --id GitHub.cli"
    elif sys.platform == "darwin":
        how = "brew install gh"
    else:
        how = "https://cli.github.com/"
    return f"The gh CLI is not installed. Install it ({how}) and run `gh auth login`."


def _limit(limit: int) -> int:
    try:
        n = int(limit or 10)
    except (TypeError, ValueError):
        n = 10
    return max(1, min(n, 50))


def _clip(out: str, command: str, number: int) -> str:
    if len(out) <= _MAX_CHARS:
        return out
    return out[:_MAX_CHARS] + (
        f"\n\n… truncated at {_MAX_CHARS} chars. Run `gh {command} {number}` "
        "in a terminal to read the rest."
    )


def _run(argv: list[str], timeout: int = _TIMEOUT) -> tuple[bool, str]:
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
    except FileNotFoundError:
        return False, _NO_CLI
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
        argv += ["--limit", str(_limit(limit))]
        argv += ["--json", _JSON_FIELDS]
    return True, argv


def _api_get(url: str, accept: str = "application/vnd.github+json") -> tuple[bool, bytes | str]:
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "paperclip"})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:  # noqa: S310
            return True, resp.read()
    except urllib.error.HTTPError as exc:
        return False, (
            f"GitHub returned HTTP {exc.code} for that public read. "
            f"Private repositories need the gh CLI. {_install_hint()}"
        )
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return False, f"could not reach GitHub ({exc}). {_install_hint()}"


def _api_rows(command: str, repo: str, limit: int) -> tuple[bool, list[dict] | str]:
    kind = "pulls" if command == "pr list" else "issues"
    url = f"{_API}/repos/{repo}/{kind}?state=open&per_page={_limit(limit)}"
    ok, body = _api_get(url)
    if not ok:
        return False, body  # type: ignore[return-value]
    try:
        data = json.loads(body)  # type: ignore[arg-type]
    except json.JSONDecodeError:
        text = body.decode("utf-8", "replace") if isinstance(body, bytes) else str(body)
        return False, f"GitHub returned something that was not JSON: {text[:200]}"
    if not isinstance(data, list):
        return False, "GitHub returned something that was not a list."
    rows = []
    for item in data:
        if command == "issue list" and "pull_request" in item:
            continue
        rows.append({
            "number": item.get("number"),
            "title": item.get("title", ""),
            "author": {"login": (item.get("user") or {}).get("login", "?")},
            "updatedAt": item.get("updated_at") or "",
            "url": item.get("html_url") or "",
        })
    return True, rows


def _api_text(command: str, number: int, repo: str) -> tuple[bool, str]:
    kind = "pulls" if command.startswith("pr") else "issues"
    if command == "pr diff":
        ok, body = _api_get(
            f"{_API}/repos/{repo}/pulls/{number}",
            accept="application/vnd.github.diff",
        )
        if not ok:
            return False, str(body)
        return True, body.decode("utf-8", "replace").strip()  # type: ignore[union-attr]
    ok, body = _api_get(f"{_API}/repos/{repo}/{kind}/{number}")
    if not ok:
        return False, str(body)
    try:
        item = json.loads(body)  # type: ignore[arg-type]
    except json.JSONDecodeError:
        text = body.decode("utf-8", "replace") if isinstance(body, bytes) else str(body)
        return False, f"GitHub returned something that was not JSON: {text[:200]}"
    who = (item.get("user") or {}).get("login", "?")
    updated = (item.get("updated_at") or "")[:10]
    text = (
        f"#{item.get('number')} {item.get('title', '')}\n"
        f"@{who} · updated {updated}\n"
        f"{item.get('html_url', '')}"
    )
    desc = (item.get("body") or "").strip()
    if desc:
        text += "\n\n" + desc
    return True, text


def _rows(command: str, repo: str, limit: int) -> tuple[bool, list[dict] | str]:
    ok, argv = _argv(command, 0, repo, limit)
    if not ok:
        return False, argv  # type: ignore[return-value]
    ok, out = _run(argv)  # type: ignore[arg-type]
    if not ok and out == _NO_CLI:
        if not repo:
            return False, _install_hint()
        return _api_rows(command, repo, limit)
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
    if not ok and out == _NO_CLI:
        if not repo:
            return _install_hint()
        ok, out = _api_text(command, number, repo)
        if not ok:
            return out
    elif not ok:
        return out
    return _clip(out, command, number)


def make_tool(default_repo: str = "") -> Tool:
    def run(command: str, number: int = 0, repo: str = "", limit: int = 10) -> str:
        return gh_read(command, number, repo or default_repo, limit)

    return Tool(
        name="github_read",
        description=(
            "Read pull requests and issues from GitHub. Uses the gh CLI when it is "
            "installed; public owner/name repos are read from the GitHub API when it is not. "
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
