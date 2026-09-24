"""Eval plumbing: fake client and make_paperclip. See docs/evals/helpers.md."""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from types import SimpleNamespace


def _has_key() -> bool:
    from paperclip.config import load_settings
    from paperclip.loop.models import PROVIDERS

    settings = load_settings()
    provider = PROVIDERS.get(settings.provider)
    return bool(settings.api_key or (provider and os.getenv(provider.key_env)))


HAS_KEY = _has_key()


def text_block(text: str):
    return SimpleNamespace(type="text", text=text)


def tool_block(name: str, args: dict, call_id: str = "tu_1"):
    return SimpleNamespace(type="tool_use", id=call_id, name=name, input=args)


def response(blocks, stop_reason="end_turn"):
    return SimpleNamespace(
        stop_reason=stop_reason,
        usage=SimpleNamespace(input_tokens=0, output_tokens=0),
        content=blocks,
    )


class ScriptedClient:
    def __init__(self, script: list):
        self._script = list(script)
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        return self._script.pop(0)


def make_paperclip(home: Path, client=None, **settings_overrides):
    from paperclip.app import Paperclip
    from paperclip.config import Settings

    known = {f.name for f in dataclasses.fields(Settings)}
    for switch in ("apple_calendar", "google_calendar", "apple_tools", "graph_workflows"):
        if switch in known:
            settings_overrides.setdefault(switch, False)
    settings = Settings(home=home, **settings_overrides)
    if client is not None and not settings.api_key:
        settings.api_key = "offline"
    return Paperclip(settings=settings, client=client)
