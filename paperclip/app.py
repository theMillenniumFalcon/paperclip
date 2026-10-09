"""Assemble one Paperclip and run a turn. See docs/app.md."""

from __future__ import annotations

from paperclip.config import Settings, load_settings
from paperclip.db import connect
from paperclip.loop.agent import LoopResult, Observer, run_loop
from paperclip.loop.models import get_client
from paperclip.memory import Memory
from paperclip.ops.tracing import Tracer, compose
from paperclip.runtime.session import Session
from paperclip.tools import build_registry


class Paperclip:
    def __init__(self, settings: Settings | None = None, client=None, conn=None):
        self.settings = settings or load_settings()
        self.settings.ensure_home()
        self.conn = conn or connect(self.settings.home)
        self.client = client or get_client(self.settings)
        self.memory = Memory(self.conn, self.settings, self.client)
        self.tools = build_registry(self.conn, self.settings, self.memory)
        self.mcp_bridge = getattr(self.tools, "mcp_bridge", None)
        self.session = Session(self.settings, memory=self.memory)
        self.tracer = Tracer(self.settings)

    def close(self) -> None:
        if self.mcp_bridge is not None:
            self.mcp_bridge.close()

    def respond(self, user_message: str, observer: Observer | None = None,
                source: str = "cli", stream: bool = False) -> LoopResult:
        notify = compose(observer, self.tracer.event)

        with self.tracer.turn(user_message):
            system = self.session.build_system(user_message, notify=notify)
            messages = list(self.session.history) + [{"role": "user", "content": user_message}]

            result = run_loop(
                client=self.client,
                model=self.settings.model,
                system=system,
                messages=messages,
                tools=self.tools,
                max_iterations=self.settings.max_iterations,
                max_tokens=self.settings.max_tokens,
                observer=notify,
                stream=stream,
            )

            self.session.add_exchange(user_message, result.reply, tool_calls=result.tool_calls,
                                      source=source)
            if self.memory is not None:
                self.memory.maybe_consolidate(notify=notify)
                self.memory.export_markdown()

        self.tracer.end_turn(result.reply, result.iterations)
        return result
