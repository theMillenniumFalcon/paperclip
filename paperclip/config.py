"""Env-backed settings. See docs/config.md."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    provider: str = field(default_factory=lambda: os.getenv("PAPERCLIP_PROVIDER", "anthropic"))
    api_key: str = field(default_factory=lambda: os.getenv("PAPERCLIP_API_KEY", ""))
    base_url: str | None = field(default_factory=lambda: os.getenv("PAPERCLIP_BASE_URL") or None)
    model: str = field(default_factory=lambda: os.getenv("PAPERCLIP_MODEL", ""))
    small_model: str = field(default_factory=lambda: os.getenv("PAPERCLIP_SMALL_MODEL", ""))
    home: Path = field(default_factory=lambda: Path(os.getenv("PAPERCLIP_HOME", ".paperclip")))
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

    def ensure_home(self) -> Path:
        self.home.mkdir(parents=True, exist_ok=True)
        (self.home / "traces").mkdir(exist_ok=True)
        (self.home / "outbox").mkdir(exist_ok=True)
        return self.home


def load_settings() -> Settings:
    return Settings()
