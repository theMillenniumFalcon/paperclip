"""LLM providers and client factory. See docs/loop/models.md."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from types import SimpleNamespace

from paperclip.config import Settings


@dataclass(frozen=True)
class Provider:
    kind: str
    key_env: str
    base_url: str | None
    model: str
    small_model: str


PROVIDERS: dict[str, Provider] = {
    "anthropic": Provider(
        "anthropic",
        "ANTHROPIC_API_KEY",
        None,
        "claude-sonnet-5",
        "claude-haiku-4-5-20251001",
    ),
    "openai": Provider(
        "openai",
        "OPENAI_API_KEY",
        None,
        "gpt-5.5",
        "gpt-4.1-mini",
    ),
    "openrouter": Provider(
        "openai",
        "OPENROUTER_API_KEY",
        "https://openrouter.ai/api/v1",
        "nvidia/nemotron-nano-9b-v2:free",
        "google/gemma-3-4b-it:free",
    ),
    "gemini": Provider(
        "openai",
        "GEMINI_API_KEY",
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
    ),
}


def retry_with_max_tokens(exc: BaseException) -> bool:
    """True only when the provider rejected `max_completion_tokens` by name.

    Rate limits, auth failures, and other request errors must surface on the
    first attempt. See docs/loop/models.md.
    """
    if type(exc).__name__ not in {"BadRequestError", "UnprocessableEntityError"}:
        return False
    return "max_completion_tokens" in str(exc).lower()


def get_client(settings: Settings):
    provider = PROVIDERS.get(settings.provider)
    if provider is None:
        raise SystemExit(
            f"Unknown PAPERCLIP_PROVIDER '{settings.provider}'. "
            f"Pick one of: {', '.join(PROVIDERS)}"
        )

    api_key = settings.api_key or os.getenv(provider.key_env, "")
    if not api_key:
        raise SystemExit(
            f"No API key for provider '{settings.provider}'. "
            f"Set {provider.key_env} in .env (see .env.example)."
        )

    settings.model = settings.model or provider.model
    settings.small_model = settings.small_model or provider.small_model
    base_url = settings.base_url or provider.base_url

    timeout = float(os.getenv("PAPERCLIP_LLM_TIMEOUT", "120"))

    if provider.kind == "anthropic":
        import anthropic

        kwargs: dict = {"api_key": api_key, "timeout": timeout}
        if base_url:
            kwargs["base_url"] = base_url
        return anthropic.Anthropic(**kwargs)
    return OpenAICompatClient(api_key=api_key, base_url=base_url, timeout=timeout)


class OpenAICompatClient:
    def __init__(self, api_key: str, base_url: str | None = None, timeout: float = 120.0):
        import openai

        self._client = openai.OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self.messages = SimpleNamespace(create=self._create, stream=self._stream)

    def _to_openai(self, *, model, messages, max_tokens, system=None, tools=None) -> dict:
        oai_messages = []
        if system:
            oai_messages.append({"role": "system", "content": system})
        for message in messages:
            content = message["content"]
            if isinstance(content, str):
                oai_messages.append({"role": message["role"], "content": content})
            elif message["role"] == "assistant":
                text = "".join(b.text for b in content if getattr(b, "type", "") == "text")
                calls = [
                    {"id": b.id, "type": "function",
                     "function": {"name": b.name, "arguments": json.dumps(b.input)}}
                    for b in content if getattr(b, "type", "") == "tool_use"
                ]
                entry: dict = {"role": "assistant", "content": text or None}
                if calls:
                    entry["tool_calls"] = calls
                oai_messages.append(entry)
            else:
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        oai_messages.append({
                            "role": "tool",
                            "tool_call_id": block["tool_use_id"],
                            "content": block["content"],
                        })

        kwargs: dict = {"model": model, "messages": oai_messages,
                        "max_completion_tokens": max_tokens}
        if tools:
            kwargs["tools"] = [
                {"type": "function",
                 "function": {"name": t["name"], "description": t["description"],
                              "parameters": t["input_schema"]}}
                for t in tools
            ]
        return kwargs

    def _call(self, kwargs: dict, **extra):
        try:
            return self._client.chat.completions.create(**kwargs, **extra)
        except Exception as exc:
            if not retry_with_max_tokens(exc):
                raise
            k = dict(kwargs)
            k["max_tokens"] = k.pop("max_completion_tokens", None)
            return self._client.chat.completions.create(**k, **extra)

    def _create(self, *, model, messages, max_tokens, system=None, tools=None):
        response = self._call(self._to_openai(
            model=model, messages=messages, max_tokens=max_tokens, system=system, tools=tools))
        choice = response.choices[0].message
        blocks = []
        if choice.content:
            blocks.append(SimpleNamespace(type="text", text=choice.content))
        for call in choice.tool_calls or []:
            blocks.append(SimpleNamespace(
                type="tool_use", id=call.id, name=call.function.name,
                input=json.loads(call.function.arguments or "{}"),
            ))
        usage = getattr(response, "usage", None)
        return SimpleNamespace(
            stop_reason="tool_use" if choice.tool_calls else "end_turn",
            usage=SimpleNamespace(
                input_tokens=getattr(usage, "prompt_tokens", 0),
                output_tokens=getattr(usage, "completion_tokens", 0),
            ),
            content=blocks,
        )

    def _stream(self, *, model, messages, max_tokens, system=None, tools=None):
        kwargs = self._to_openai(
            model=model, messages=messages, max_tokens=max_tokens, system=system, tools=tools)
        return _OpenAIStream(self, kwargs)


class _OpenAIStream:
    def __init__(self, client: OpenAICompatClient, kwargs: dict):
        self._client = client
        self._kwargs = kwargs
        self._text: list[str] = []
        self._tools: dict[int, dict] = {}
        self._usage = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    @property
    def text_stream(self):
        stream = self._client._call(
            self._kwargs, stream=True, stream_options={"include_usage": True})
        for chunk in stream:
            if getattr(chunk, "usage", None):
                self._usage = chunk.usage
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if getattr(delta, "content", None):
                self._text.append(delta.content)
                yield delta.content
            for tc in (getattr(delta, "tool_calls", None) or []):
                slot = self._tools.setdefault(tc.index, {"id": None, "name": "", "args": ""})
                if tc.id:
                    slot["id"] = tc.id
                if tc.function and tc.function.name:
                    slot["name"] = tc.function.name
                if tc.function and tc.function.arguments:
                    slot["args"] += tc.function.arguments

    def get_final_message(self):
        blocks = []
        text = "".join(self._text)
        if text:
            blocks.append(SimpleNamespace(type="text", text=text))
        for slot in self._tools.values():
            blocks.append(SimpleNamespace(
                type="tool_use", id=slot["id"], name=slot["name"],
                input=json.loads(slot["args"] or "{}")))
        usage = self._usage
        return SimpleNamespace(
            stop_reason="tool_use" if self._tools else "end_turn",
            usage=SimpleNamespace(
                input_tokens=getattr(usage, "prompt_tokens", 0),
                output_tokens=getattr(usage, "completion_tokens", 0)),
            content=blocks,
        )
