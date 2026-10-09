"""Build the tool registry. See docs/tools/README.md."""

from __future__ import annotations

import os
import sqlite3

from paperclip.config import Settings
from paperclip.tools import calendar, memory_admin, messages, notes, search
from paperclip.tools.registry import ToolRegistry


def build_registry(conn: sqlite3.Connection, settings: Settings, memory=None) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(calendar.make_tool(conn, settings.home, apple_calendar=settings.apple_calendar))
    registry.register(calendar.make_list_tool(conn))
    registry.register(notes.make_tool(conn))
    registry.register(messages.make_tool(settings.home))
    registry.register(search.make_tool())

    if memory is not None:
        registry.register(memory_admin.make_manage_memory_tool(memory))
        registry.register(memory_admin.make_update_soul_tool(settings))
        registry.register(memory_admin.make_create_skill_tool(settings, memory))

    if os.getenv("PAPERCLIP_EXPERIMENTAL", "") in ("1", "true", "yes"):
        from paperclip.tools import experimental

        for t in experimental.make_tools():
            registry.register(t)

    if settings.apple_tools:
        from paperclip.tools import apple

        for t in apple.make_tools():
            registry.register(t)

    mcp_config = settings.home / "mcp.json"
    if mcp_config.exists():
        try:
            from paperclip.tools.mcp_client import MCPBridge

            bridge = MCPBridge(mcp_config)
            for t in bridge.start():
                registry.register(t)
            registry.mcp_bridge = bridge
        except ImportError:
            print("mcp.json found but the 'mcp' package is missing — pip install 'paperclip[mcp]'")

    return registry
