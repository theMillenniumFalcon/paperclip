"""Configuration — every knob is an env var, documented in .env.example.

No settings framework: a dataclass read once at startup.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import find_dotenv, load_dotenv


def _load_env() -> str:
    path = find_dotenv(usecwd=True)
    if path:
        load_dotenv(path)
    return path


DOTENV_PATH = _load_env()


@dataclass
class Settings:
    # --- LLM: pick a provider, set its key. See paperclip/loop/models.py PROVIDERS.
    provider: str = field(default_factory=lambda: os.getenv("PAPERCLIP_PROVIDER", "anthropic"))
    # Explicit overrides (optional): key, endpoint, and model ids. Left empty,
    # the provider's own key env var and default models are used.
    api_key: str = field(default_factory=lambda: os.getenv("PAPERCLIP_API_KEY", ""))
    base_url: str | None = field(default_factory=lambda: os.getenv("PAPERCLIP_BASE_URL") or None)
    model: str = field(default_factory=lambda: os.getenv("PAPERCLIP_MODEL", ""))
    gh_tool: bool = field(
        default_factory=lambda: os.getenv("PAPERCLIP_GH_TOOL", "").lower() in ("1", "true", "yes")
    )
    home: Path = field(default_factory=lambda: Path(os.getenv("PAPERCLIP_HOME", ".paperclip")))

    def ensure_home(self) -> Path:
        self.home.mkdir(parents=True, exist_ok=True)
        (self.home / "traces").mkdir(exist_ok=True)
        (self.home / "outbox").mkdir(exist_ok=True)
        return self.home


def load_settings() -> Settings:
    return Settings()