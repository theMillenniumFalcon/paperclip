"""Agent turn loop (reason → act). See docs/loop/agent.md."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import anthropic

from paperclip.loop.errors import log_provider_error, provider_detail, provider_error_reply
from paperclip.tools.registry import ToolRegistry

LoopEvent = dict[str, Any]
Observer = Callable[[str, LoopEvent], None]


@dataclass
class LoopResult:
    reply: str
    tool_calls: list[LoopEvent] = field(default_factory=list)
    iterations: int = 0
    error: str | None = None


def run_loop(
    client: anthropic.Anthropic,
    model: str,
    system: str,
    messages: list[dict],
    tools: ToolRegistry,
    max_iterations: int = 10,
    max_tokens: int = 2048,
    observer: Observer | None = None,
    stream: bool = False,
) -> LoopResult:
    notify = observer or (lambda kind, ev: None)
    result = LoopResult(reply="")
    can_stream = stream and hasattr(client.messages, "stream")

    for iteration in range(1, max_iterations + 1):
        result.iterations = iteration

        try:
            response = _complete(
                client, model, system, messages, tools, max_tokens, can_stream, notify,
            )
        except Exception as exc:
            reply = provider_error_reply(exc)
            if reply is None:
                raise
            log_provider_error(exc)
            notify("error", {"error": type(exc).__name__, "detail": provider_detail(exc)})
            result.reply = reply
            result.error = type(exc).__name__
            return result
        notify("llm", {"iteration": iteration, "stop_reason": response.stop_reason,
                       "usage": {"in": response.usage.input_tokens, "out": response.usage.output_tokens}})

        messages.append({"role": "assistant", "content": response.content})

        tool_uses = [b for b in response.content if b.type == "tool_use"]

        if not tool_uses:
            result.reply = "".join(b.text for b in response.content if b.type == "text")
            return result

        tool_results = []
        for call in tool_uses:
            output = tools.execute(call.name, call.input)
            event = {"tool": call.name, "args": call.input, "output": output}
            result.tool_calls.append(event)
            notify("tool", event)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": call.id, "content": output}
            )
        messages.append({"role": "user", "content": tool_results})

    result.reply = "(I hit my iteration limit before finishing — try breaking the request into smaller steps.)"
    return result


def _complete(client, model, system, messages, tools, max_tokens, can_stream, notify):
    response = None
    if can_stream:
        try:
            with client.messages.stream(
                model=model, system=system, messages=messages,
                tools=tools.schemas(), max_tokens=max_tokens,
            ) as s:
                for delta in s.text_stream:
                    notify("text", {"delta": delta})
                response = s.get_final_message()
        except Exception as exc:
            if provider_error_reply(exc) is not None:
                raise
            response = None
    if response is None:
        response = client.messages.create(
            model=model,
            system=system,
            messages=messages,
            tools=tools.schemas(),
            max_tokens=max_tokens,
        )
    return response
