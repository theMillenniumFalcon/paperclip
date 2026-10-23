"""GitHub allowlist. See docs/evals/deterministic.md."""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from paperclip.tools.github import gh_read, make_tool

_REPO = "octocat/Hello-World"


def _ok(stdout: str):
    def run(argv, **kwargs):
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    return run


@pytest.mark.parametrize(
    "command",
    ["pr merge", "pr comment", "issue close", "api", "pr create", "repo delete"],
)
def test_write_commands_never_reach_a_subprocess(command):
    with patch("paperclip.tools.github.subprocess.run") as run:
        out = gh_read(command, number=1, repo=_REPO)
    run.assert_not_called()
    assert "read-only" in out
    assert "pr list" in out and "issue view" in out


def test_hostile_repo_never_reaches_a_subprocess():
    with patch("paperclip.tools.github.subprocess.run") as run:
        injected = gh_read("pr list", repo="octocat/Hello-World; rm -rf ~")
        flagged = gh_read("pr view", number=1, repo="-x/y")
    run.assert_not_called()
    assert "not a valid repo" in injected
    assert "not a valid repo" in flagged


def test_view_and_diff_need_a_positive_number():
    with patch("paperclip.tools.github.subprocess.run") as run:
        missing = gh_read("pr view", repo=_REPO)
        zero = gh_read("pr diff", number=0, repo=_REPO)
        bad = gh_read("issue view", number="nope", repo=_REPO)  # type: ignore[arg-type]
    run.assert_not_called()
    assert "needs a positive" in missing and "needs a positive" in zero
    assert "needs a PR/issue number" in bad


def test_list_argv_is_built_from_the_allowlist():
    payload = (
        '[{"number": 7, "title": "Fix the lock", "author": {"login": "ada"}, '
        '"updatedAt": "2026-10-01T12:00:00Z", "url": "https://example.test/7"}]'
    )
    with patch("paperclip.tools.github.subprocess.run", side_effect=_ok(payload)) as run:
        out = gh_read("pr list", repo=_REPO, limit=99)
    argv = run.call_args.args[0]
    assert argv == [
        "gh", "pr", "list", "--repo", _REPO, "--limit", "50",
        "--json", "number,title,author,updatedAt,url",
    ]
    assert run.call_args.kwargs.get("shell", False) is False
    assert run.call_args.kwargs["timeout"] == 20
    assert run.call_args.kwargs["check"] is False
    assert "#7 Fix the lock — @ada (updated 2026-10-01)" in out


def test_limit_default_and_clamp():
    with patch("paperclip.tools.github.subprocess.run", side_effect=_ok("[]")) as run:
        out = gh_read("issue list", repo=_REPO, limit=0)
    assert run.call_args.args[0][run.call_args.args[0].index("--limit") + 1] == "10"
    assert out == "(none open)"
    with patch("paperclip.tools.github.subprocess.run", side_effect=_ok("[]")) as run:
        gh_read("issue list", repo=_REPO, limit=-3)
    assert run.call_args.args[0][run.call_args.args[0].index("--limit") + 1] == "1"


def test_view_argv_and_truncation():
    with patch("paperclip.tools.github.subprocess.run", side_effect=_ok("x" * 8001)) as run:
        out = gh_read("pr diff", number=12, repo=_REPO)
    assert run.call_args.args[0] == ["gh", "pr", "diff", "12", "--repo", _REPO]
    assert out.startswith("x" * 8000)
    assert "truncated at 8000" in out
    assert "gh pr diff 12" in out


def test_default_repo_fills_an_omitted_repo():
    with patch("paperclip.tools.github.subprocess.run", side_effect=_ok("[]")) as run:
        make_tool(_REPO).fn(command="issue list")
    assert "--repo" in run.call_args.args[0]
    assert run.call_args.args[0][run.call_args.args[0].index("--repo") + 1] == _REPO


def test_explicit_repo_overrides_the_default():
    other = "octocat/Spoon-Knife"
    with patch("paperclip.tools.github.subprocess.run", side_effect=_ok("body")) as run:
        make_tool(_REPO).fn(command="issue view", number=3, repo=other)
    assert run.call_args.args[0] == ["gh", "issue", "view", "3", "--repo", other]


class _Body:
    def __init__(self, payload: bytes):
        self.payload = payload

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_missing_cli_without_a_repo_names_the_installer():
    with patch("paperclip.tools.github.subprocess.run", side_effect=FileNotFoundError), \
         patch("paperclip.tools.github.urllib.request.urlopen") as urlopen:
        missing = gh_read("pr list")
    urlopen.assert_not_called()
    assert "not installed" in missing and "gh auth login" in missing
    if sys.platform == "win32":
        assert "winget install --id GitHub.cli" in missing
    elif sys.platform == "darwin":
        assert "brew install gh" in missing
    else:
        assert "https://cli.github.com/" in missing


def test_missing_cli_lists_public_pulls():
    payload = json.dumps([{
        "number": 3,
        "title": "Add wake word",
        "user": {"login": "sean"},
        "updated_at": "2026-10-02T00:00:00Z",
        "html_url": "https://github.com/octocat/Hello-World/pull/3",
    }]).encode()
    with patch("paperclip.tools.github.subprocess.run", side_effect=FileNotFoundError), \
         patch("paperclip.tools.github.urllib.request.urlopen", return_value=_Body(payload)) as urlopen:
        out = gh_read("pr list", repo=_REPO, limit=10)
    assert "#3 Add wake word — @sean (updated 2026-10-02)" in out
    req = urlopen.call_args.args[0]
    assert req.full_url == (
        "https://api.github.com/repos/octocat/Hello-World/pulls?state=open&per_page=10"
    )
    assert req.get_header("User-agent") == "paperclip"


def test_public_issue_list_drops_pull_requests():
    payload = json.dumps([
        {"number": 1, "title": "Bug", "user": {"login": "a"},
         "updated_at": "2026-01-01T00:00:00Z", "html_url": "https://example.test/1"},
        {"number": 2, "title": "PR", "user": {"login": "b"},
         "updated_at": "2026-01-02T00:00:00Z", "html_url": "https://example.test/2",
         "pull_request": {}},
    ]).encode()
    with patch("paperclip.tools.github.subprocess.run", side_effect=FileNotFoundError), \
         patch("paperclip.tools.github.urllib.request.urlopen", return_value=_Body(payload)):
        out = gh_read("issue list", repo=_REPO)
    assert "#1 Bug — @a (updated 2026-01-01)" in out
    assert "#2" not in out


def test_timeout_and_auth():

    import subprocess

    with patch(
        "paperclip.tools.github.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd=["gh"], timeout=20),
    ):
        timed = gh_read("pr list", repo=_REPO)
    assert "timed out after 20s" in timed

    def auth_fail(argv, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="HTTP 401: authentication required")

    with patch("paperclip.tools.github.subprocess.run", side_effect=auth_fail):
        denied = gh_read("pr view", number=1, repo=_REPO)
    assert "not authenticated" in denied


def test_non_json_list_is_a_sentence():
    with patch("paperclip.tools.github.subprocess.run", side_effect=_ok("not-json")):
        out = gh_read("issue list", repo=_REPO)
    assert out.startswith("gh returned something that was not JSON:")


def test_registry_registers_github_read(tmp_path):
    from paperclip.config import Settings
    from paperclip.db import connect
    from paperclip.tools import build_registry

    settings = Settings(home=tmp_path, github_repo=_REPO, api_key="offline")
    registry = build_registry(connect(tmp_path), settings)
    names = [item["name"] for item in registry.schemas()]
    assert "github_read" in names
