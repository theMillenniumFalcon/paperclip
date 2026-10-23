"""Env-backed settings. See docs/config.md."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values


def default_home() -> Path:
    """User home on every OS: ~/.paperclip, which is %USERPROFILE%\\.paperclip on Windows."""
    return Path.home() / ".paperclip"


def _template_text() -> str:
    packaged = Path(__file__).with_name("env.example")
    if packaged.is_file():
        return packaged.read_text(encoding="utf-8")
    root = Path(__file__).resolve().parents[1] / ".env.example"
    if root.is_file():
        return root.read_text(encoding="utf-8")
    return "ANTHROPIC_API_KEY=\n"


def _apply_env_file(path: Path) -> None:
    """Fill variables that are still unset. A blank value does not count as set."""
    if not path.is_file():
        return
    for key, value in dotenv_values(path).items():
        if not key or value is None or value == "":
            continue
        os.environ.setdefault(key, value)


def resolve_home() -> Path:
    """Home folder. A project .env may set PAPERCLIP_HOME when the shell did not."""
    if not (os.getenv("PAPERCLIP_HOME") or "").strip():
        cwd_env = Path.cwd() / ".env"
        if cwd_env.is_file():
            value = (dotenv_values(cwd_env).get("PAPERCLIP_HOME") or "").strip()
            if value:
                os.environ["PAPERCLIP_HOME"] = value
    raw = (os.getenv("PAPERCLIP_HOME") or "").strip()
    return Path(raw).expanduser() if raw else default_home()


def env_file() -> Path:
    return resolve_home() / ".env"


def load_env() -> Path:
    """Load the home .env, then a project .env for keys the home file left unset.

    The first launch copies .env.example into the home folder.
    """
    home = resolve_home()
    home.mkdir(parents=True, exist_ok=True)
    path = home / ".env"
    if not path.exists():
        path.write_text(_template_text(), encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass
    _apply_env_file(path)
    cwd_env = Path.cwd() / ".env"
    try:
        same = cwd_env.is_file() and cwd_env.resolve() == path.resolve()
    except OSError:
        same = False
    if cwd_env.is_file() and not same:
        _apply_env_file(cwd_env)
    return path


load_env()


@dataclass
class Settings:
    provider: str = field(default_factory=lambda: os.getenv("PAPERCLIP_PROVIDER", "anthropic"))
    api_key: str = field(default_factory=lambda: os.getenv("PAPERCLIP_API_KEY", ""))
    base_url: str | None = field(default_factory=lambda: os.getenv("PAPERCLIP_BASE_URL") or None)
    model: str = field(default_factory=lambda: os.getenv("PAPERCLIP_MODEL", ""))
    small_model: str = field(default_factory=lambda: os.getenv("PAPERCLIP_SMALL_MODEL", ""))
    home: Path = field(default_factory=resolve_home)
    max_iterations: int = field(default_factory=lambda: int(os.getenv("PAPERCLIP_MAX_ITERATIONS", "10")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("PAPERCLIP_MAX_TOKENS", "2048")))
    consolidate_every: int = field(default_factory=lambda: int(os.getenv("PAPERCLIP_CONSOLIDATE_EVERY", "6")))
    retrieval_top_k: int = field(default_factory=lambda: int(os.getenv("PAPERCLIP_RETRIEVAL_TOP_K", "4")))
    semantic_store: str = field(default_factory=lambda: os.getenv("PAPERCLIP_SEMANTIC_STORE", "sqlite"))
    apple_calendar: bool = field(
        default_factory=lambda: os.getenv("PAPERCLIP_APPLE_CALENDAR", "") in ("1", "true", "yes")
    )
    apple_tools: bool = field(
        default_factory=lambda: os.getenv("PAPERCLIP_APPLE_TOOLS", "") in ("1", "true", "yes")
    )
    telegram_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    otel_endpoint: str = field(
        default_factory=lambda: os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    )
    github_repo: str = field(default_factory=lambda: os.getenv("PAPERCLIP_GITHUB_REPO", ""))

    def ensure_home(self) -> Path:
        self.home.mkdir(parents=True, exist_ok=True)
        (self.home / "traces").mkdir(exist_ok=True)
        (self.home / "outbox").mkdir(exist_ok=True)
        return self.home


def load_settings() -> Settings:
    load_env()
    return Settings()
