"""Offline and live eval helpers. See docs/evals/helpers.md."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

HAS_KEY = bool(os.getenv("ANTHROPIC_API_KEY"))


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

    settings_overrides.setdefault("apple_calendar", False)
    settings = Settings(home=home, **settings_overrides)
    if client is not None and not settings.api_key:
        settings.api_key = "offline"
    return Paperclip(settings=settings, client=client)
