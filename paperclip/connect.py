"""User-initiated browser sign-in for integrations. See docs/connect.md."""

from __future__ import annotations

import importlib
from pathlib import Path

CONNECTORS = {
    "google": "paperclip.tools.google_calendar:connect",
    "paperclip-memory": "paperclip.tools.paperclip_memory:connect",
}


def usage() -> str:
    return "Usage: paperclip connect <name>  —  available: " + ", ".join(sorted(CONNECTORS)) + "."


def connect(name: str, home: Path) -> str:
    target = CONNECTORS.get(name.strip().lower())
    if target is None:
        return f"Nothing called '{name}' to connect. " + usage()
    module_name, _, fn_name = target.partition(":")
    return getattr(importlib.import_module(module_name), fn_name)(home)


def cli_main(argv: list[str]) -> int:
    if not argv or argv[0].strip().lower() not in CONNECTORS:
        print(usage() if not argv else connect(argv[0], Path()))
        return 1
    from paperclip.config import load_settings

    settings = load_settings()
    settings.ensure_home()
    print(connect(argv[0], settings.home))
    return 0
