"""Stub tools gated by PAPERCLIP_EXPERIMENTAL. See docs/tools/experimental.md."""

from __future__ import annotations

from paperclip.tools.registry import Tool

PLANNED = [
    {"name": "delegate_task", "box": "Sub-Agents",
     "description": "Spawn a fresh agent run for a self-contained subtask and return its "
                    "result. Left out to keep the core single-agent and readable."},
    {"name": "run_command", "box": "Terminal tool",
     "description": "Run a shell command in a sandbox and read the output. "
                    "Needs a real sandbox + safety surface first."},
    {"name": "browse_web", "box": "Browser tool",
     "description": "Open a page and read/click it. (search_web already covers read-only web lookups.)"},
    {"name": "schedule_task", "box": "Cron Job",
     "description": "Let the agent schedule its own recurring runs. A system cron can already "
                    "call a brief command; this would move scheduling in-app."},
]


def _stub(name: str, description: str, box: str) -> Tool:
    def fn(**kwargs) -> str:
        return (f"'{name}' maps to the '{box}' capability and isn't wired "
                f"in yet — it's on the roadmap (coming soon). Tell the user honestly.")

    return Tool(name=name, description=f"[coming soon] {description}",
                input_schema={"type": "object", "properties": {}}, fn=fn)


def make_tools() -> list[Tool]:
    return [_stub(p["name"], p["description"], p["box"]) for p in PLANNED]
