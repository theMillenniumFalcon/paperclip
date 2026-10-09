"""Whether a turn should search memory. See docs/memory/retrieval-gate.md."""

from __future__ import annotations

import json

import anthropic

GATE_PROMPT = """\
You are a retrieval gate for a personal assistant's long-term memory.
Given the user's message, decide if answering well requires the user's stored
memories (facts about people, projects, preferences, or past events).

Reply with ONLY this JSON, nothing else:
{{"retrieve": true/false, "query": "<search keywords if true, else empty>", "reason": "<5 words>"}}

General knowledge, math, small talk, or self-contained requests → false.
Anything referencing the user's life, people, plans, or history → true.

User message: {message}"""


def should_retrieve(
    client: anthropic.Anthropic, small_model: str, message: str
) -> tuple[bool, str, str]:
    try:
        response = client.messages.create(
            model=small_model,
            max_tokens=100,
            messages=[{"role": "user", "content": GATE_PROMPT.format(message=message)}],
        )
        text = "".join(b.text for b in response.content if b.type == "text")
        decision = json.loads(text[text.index("{") : text.rindex("}") + 1])
        return bool(decision.get("retrieve")), decision.get("query", message), decision.get("reason", "")
    except Exception as exc:
        return True, message, f"gate failed open ({type(exc).__name__})"
