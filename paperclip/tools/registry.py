"""Name + schema + function the model can call. See docs/tools/registry.md."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    fn: Callable[..., str]
    wants_notify: bool = False

    def to_api(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def schemas(self) -> list[dict[str, Any]]:
        return [t.to_api() for t in self._tools.values()]

    def execute(self, name: str, args: dict[str, Any], notify=None) -> str:
        tool = self._tools.get(name)
        if tool is None:
            return f"Error: unknown tool '{name}'"
        try:
            if tool.wants_notify:
                return tool.fn(**args, _notify=notify or (lambda kind, ev: None))
            return tool.fn(**args)
        except Exception as exc:
            return f"Error running {name}: {exc}"
