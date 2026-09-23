"""Dated folders for delegated coding runs. See docs/tools/workspace.md."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from paperclip.tools._env import delegate_env as _delegate_env

WORKSPACE_ENV = "PAPERCLIP_WORKSPACE"
AUTORUN_ENV = "PAPERCLIP_DELEGATE_AUTORUN"
RUN_TIMEOUT = int(os.getenv("PAPERCLIP_AUTORUN_TIMEOUT", "30"))
_OURS = {"MANIFEST.md", "run.log", "pi-transcript.log"}
_ENTRY_PREFS = ("main.py", "app.py", "run.py", "game.py")


def workspace_root() -> Path:
    return Path(os.getenv(WORKSPACE_ENV, "paperclip_workspace")).expanduser().resolve()


def _slug(text: str, n: int = 4) -> str:
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return "-".join(words[:n]) or "task"


def new_run_folder(model: str, task: str, now: datetime | None = None) -> Path:
    now = now or datetime.now()
    name = f"{now.strftime('%H%M%S')}-{_slug(model, 2)}-{_slug(task)}"
    folder = workspace_root() / now.strftime("%Y-%m-%d") / name
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def created_files(folder: Path) -> list[Path]:
    files = [p for p in folder.rglob("*")
             if p.is_file() and p.name not in _OURS and "__pycache__" not in p.parts]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def _pick_entry(files: list[Path]) -> Path | None:
    py = [p for p in files if p.suffix == ".py"]
    if not py:
        return None
    by_name = {p.name: p for p in py}
    for pref in _ENTRY_PREFS:
        if pref in by_name:
            return by_name[pref]
    with_main = [p for p in py if "__main__" in p.read_text(encoding="utf-8", errors="ignore")]
    if with_main:
        return with_main[0]
    return py[0] if len(py) == 1 else None


def autorun(folder: Path) -> tuple | None:
    if os.getenv(AUTORUN_ENV, "1") in ("0", "false", "no"):
        return None
    entry = _pick_entry(created_files(folder))
    if entry is None:
        return None
    t0 = time.perf_counter()
    try:
        r = subprocess.run([sys.executable, entry.name], cwd=folder,
                           stdin=subprocess.DEVNULL, capture_output=True, text=True,
                           timeout=RUN_TIMEOUT, check=False, env=_delegate_env())
        out = (r.stdout + r.stderr).strip()
        result = (entry.name, r.returncode, out, round(time.perf_counter() - t0, 1))
    except subprocess.TimeoutExpired:
        result = (entry.name, None,
                  f"(still running after {RUN_TIMEOUT}s — likely interactive; stopped)",
                  RUN_TIMEOUT)
    except OSError as exc:
        result = (entry.name, -1, f"couldn't launch: {exc}", 0.0)
    (folder / "run.log").write_text(
        f"$ python3 {result[0]}\nexit: {result[1]}\n\n{result[2]}\n", encoding="utf-8")
    return result


def write_manifest(folder: Path, provider: str, model: str, task: str,
                   files: list[Path], run: tuple | None) -> None:
    when = f"{folder.parent.name} {folder.name.split('-')[0]}"
    lines = [f"# Delegated coding run — {when}", "",
             f"- Model: `{provider}:{model}`",
             f"- Task: {task}", "", "## Files created"]
    lines += [f"- `{p.relative_to(folder)}` ({p.stat().st_size} bytes)" for p in files] or ["- (none)"]
    if run is not None:
        entry, code, out, secs = run
        status = "still running (interactive?)" if code is None else f"exit {code}"
        lines += ["", f"## Auto-run: `python3 {entry}` — {status} in {secs}s", "",
                  "```", out[:2000], "```"]
    (folder / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
