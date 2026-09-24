"""Offline tests for github.gh_read read-only boundary. See docs/evals/deterministic/gh-tool.md."""

from __future__ import annotations

import inspect
import subprocess

import pytest

from paperclip.tools import github


class Boom(Exception):
    pass


@pytest.fixture
def no_subprocess(monkeypatch):
    def explode(*a, **k):
        raise Boom(f"a subprocess was spawned: {a!r}")

    monkeypatch.setattr(github.subprocess, "run", explode)


@pytest.fixture
def capture(monkeypatch):
    seen: dict = {}

    def fake(argv, **kwargs):
        seen["argv"] = argv
        seen["kwargs"] = kwargs
        return subprocess.CompletedProcess(argv, 0, stdout=seen.get("stdout", "[]"), stderr="")

    monkeypatch.setattr(github.subprocess, "run", fake)
    return seen


@pytest.mark.parametrize("command", [
    "pr merge", "pr create", "pr close", "pr comment", "pr edit",
    "issue close", "issue create", "issue comment",
    "repo delete", "api", "auth token", "", "pr", "PR LIST",
])
def test_write_commands_never_reach_a_subprocess(command, no_subprocess):
    out = github.gh_read(command, number=1)
    assert "read-only" in out.lower(), out
    assert "pr list" in out, "the refusal should name what IS allowed"


def test_the_allowlist_is_exactly_the_five_read_commands():
    assert set(github._ALLOWED) == {
        "pr list", "pr view", "pr diff", "issue list", "issue view",
    }
    for argv in github._ALLOWED.values():
        assert not ({"merge", "close", "create", "comment", "edit", "delete"} & set(argv))


def test_a_hostile_repo_is_refused_not_escaped(no_subprocess):
    for bad in ("owner/repo; rm -rf ~", "--repo=x", "owner", "a/b/c", "$(whoami)/x", "-x/y"):
        out = github.gh_read("pr list", repo=bad)
        assert "not a valid repo" in out, (bad, out)


def test_view_and_diff_require_a_real_number(no_subprocess):
    for command in ("pr view", "pr diff", "issue view"):
        assert "number" in github.gh_read(command, number=0)
        assert "number" in github.gh_read(command, number=-3)
        assert "number" in github.gh_read(command, number="not-a-number")  # type: ignore[arg-type]


def test_argv_is_built_from_literals(capture):
    github.gh_read("pr view", number=42, repo="themillenniumfalcon/paperclip")
    argv = capture["argv"]
    assert argv[:3] == ["gh", "pr", "view"]
    assert argv[3] == "42", "the number must be placed by us, as its own element"
    assert argv[4:6] == ["--repo", "themillenniumfalcon/paperclip"]


def test_list_commands_ask_for_json_and_clamp_the_limit(capture):
    github.gh_read("pr list", limit=9999)
    argv = capture["argv"]
    assert "--json" in argv, "list output is parsed, so it must be requested as JSON"
    assert argv[argv.index("--limit") + 1] == "50", "an unbounded limit must be clamped"
    github.gh_read("issue list", limit=0)
    assert capture["argv"][capture["argv"].index("--limit") + 1] == "10"


def _code_lines(module) -> list[str]:
    import ast

    src = inspect.getsource(module)
    doc_spans: set[int] = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            doc_spans.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
    return [ln for i, ln in enumerate(src.splitlines(), 1)
            if i not in doc_spans and not ln.strip().startswith("#")]


def test_no_shell_true_anywhere():
    offenders = [ln.strip() for ln in _code_lines(github) if "shell=True" in ln]
    assert offenders == [], offenders


def test_every_gh_call_is_bounded(capture):
    sig = inspect.signature(github._run)
    assert sig.parameters["timeout"].default, "_run must always have a timeout default"
    github.gh_read("pr list")
    assert capture["kwargs"].get("timeout"), "the timeout must reach subprocess.run"


@pytest.mark.parametrize("exc,expect", [
    (FileNotFoundError(), "not installed"),
    (subprocess.TimeoutExpired(cmd="gh", timeout=20), "timed out"),
])
def test_failures_return_a_sentence_and_never_raise(monkeypatch, exc, expect):
    def raiser(*a, **k):
        raise exc

    monkeypatch.setattr(github.subprocess, "run", raiser)
    out = github.gh_read("pr list")
    assert expect in out, out


def test_an_unauthenticated_gh_says_how_to_fix_it(monkeypatch):
    monkeypatch.setattr(github.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
        a[0], 1, stdout="", stderr="gh auth login required to use this command"))
    out = github.gh_read("pr list")
    assert "gh auth login" in out


def test_a_huge_diff_is_truncated_by_the_tool(monkeypatch):
    monkeypatch.setattr(github.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
        a[0], 0, stdout="x" * 200_000, stderr=""))
    out = github.gh_read("pr diff", number=1)
    assert len(out) < github._MAX_CHARS + 300
    assert "truncated" in out


def test_list_helpers_return_rows_for_the_router(monkeypatch):
    payload = '[{"number":42,"title":"Fix the thing","author":{"login":"octocat"},' \
              '"updatedAt":"2026-07-31T10:00:00Z","url":"http://x"}]'
    monkeypatch.setattr(github.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
        a[0], 0, stdout=payload, stderr=""))
    ok, rows = github.list_prs("themillenniumfalcon/paperclip")
    assert ok and isinstance(rows, list) and rows[0]["number"] == 42
    assert "#42 Fix the thing — @octocat" in github.gh_read("pr list")


def test_malformed_json_does_not_raise(monkeypatch):
    monkeypatch.setattr(github.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
        a[0], 0, stdout="<html>rate limited</html>", stderr=""))
    ok, res = github.list_prs()
    assert ok is False
    assert "not JSON" in str(res)


def test_the_tool_is_off_unless_asked_for(tmp_path):
    from evals.helpers import ScriptedClient, make_paperclip

    off = make_paperclip(tmp_path / "off", client=ScriptedClient([]), gh_tool=False)
    assert "github_read" not in off.tools._tools
    on = make_paperclip(tmp_path / "on", client=ScriptedClient([]), gh_tool=True)
    assert "github_read" in on.tools._tools


def test_the_description_tells_the_model_the_boundary():
    desc = github.make_tool().description.lower()
    assert "read-only" in desc
    for verb in ("merge", "comment", "close"):
        assert verb in desc
