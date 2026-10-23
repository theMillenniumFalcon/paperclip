"""Home directory and .env precedence. See docs/evals/deterministic.md."""

from __future__ import annotations

import os
from pathlib import Path

from paperclip.config import default_home, load_env, resolve_home


def test_default_home_is_user_paperclip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PAPERCLIP_HOME", raising=False)
    assert resolve_home() == default_home()
    assert default_home() == Path.home() / ".paperclip"


def test_project_env_can_set_home_when_shell_did_not(tmp_path, monkeypatch):
    target = tmp_path / "custom-home"
    project = tmp_path / "project"
    project.mkdir()
    (project / ".env").write_text(f'PAPERCLIP_HOME="{target.as_posix()}"\n', encoding="utf-8")
    monkeypatch.chdir(project)
    monkeypatch.delenv("PAPERCLIP_HOME", raising=False)
    assert resolve_home() == target


def test_home_env_beats_project_env_and_blank_values_do_not_block(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    (home / ".env").write_text(
        "ANTHROPIC_API_KEY=\nPAPERCLIP_MODEL=from-home\n",
        encoding="utf-8",
    )
    project = tmp_path / "project"
    project.mkdir()
    (project / ".env").write_text(
        "ANTHROPIC_API_KEY=from-project\nPAPERCLIP_MODEL=from-project\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(project)
    monkeypatch.setenv("PAPERCLIP_HOME", str(home))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("PAPERCLIP_MODEL", raising=False)
    load_env()
    assert os.environ["ANTHROPIC_API_KEY"] == "from-project"
    assert os.environ["PAPERCLIP_MODEL"] == "from-home"


def test_shell_beats_env_files(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    (home / ".env").write_text("ANTHROPIC_API_KEY=from-home\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PAPERCLIP_HOME", str(home))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-shell")
    load_env()
    assert os.environ["ANTHROPIC_API_KEY"] == "from-shell"


def test_first_launch_copies_template_and_does_not_overwrite(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PAPERCLIP_HOME", str(home))
    path = load_env()
    assert path == home / ".env"
    assert "ANTHROPIC_API_KEY" in path.read_text(encoding="utf-8")
    path.write_text("ANTHROPIC_API_KEY=kept\n", encoding="utf-8")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "kept")
    load_env()
    assert path.read_text(encoding="utf-8") == "ANTHROPIC_API_KEY=kept\n"
