"""Assemble a Paperclip for evals: settings, optional client, tools."""

from __future__ import annotations

from paperclip.config import Settings, load_settings
from paperclip.loop.models import get_client
from paperclip.tools.github import make_tool
from paperclip.tools.registry import ToolRegistry


class Paperclip:
    def __init__(self, settings: Settings | None = None, client=None):
        self.settings = settings or load_settings()
        self.settings.ensure_home()
        self.client = client or get_client(self.settings)
        self.tools = ToolRegistry()
        if self.settings.gh_tool:
            self.tools.register(make_tool())
