"""LLM providers and Anthropic-shaped client. See docs/loop/models.md."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from types import SimpleNamespace

from paperclip.config import Settings


@dataclass(frozen=True)
class ProviderEndpoint:
    label: str
    base_url: str
    catalog_url: str | None = None


@dataclass(frozen=True)
class Provider:
    kind: str
    key_env: str
    base_url: str | None
    model: str
    small_model: str
    catalog_url: str | None = None
    flagship: str = ""
    fast: str = ""
    base_url_env: str = ""
    endpoints: tuple[ProviderEndpoint, ...] = ()

    def default_pair(self) -> list[str]:
        pair = [self.flagship or self.model, self.fast or self.small_model]
        return list(dict.fromkeys(m for m in pair if m))

    def configured_base_url(self) -> str | None:
        configured = os.getenv(self.base_url_env, "").strip() if self.base_url_env else ""
        return configured or self.base_url

    def catalog_for(self, base_url: str | None) -> str | None:
        normalized = (base_url or "").rstrip("/")
        for endpoint in self.endpoints:
            if endpoint.base_url.rstrip("/") == normalized:
                return endpoint.catalog_url
        return self.catalog_url


PROVIDERS: dict[str, Provider] = {
    "anthropic": Provider("anthropic", "ANTHROPIC_API_KEY", None,
                          "claude-sonnet-5", "claude-haiku-4-5-20251001",
                          catalog_url="https://api.anthropic.com/v1/models",
                          flagship="claude-opus-4-8", fast="claude-sonnet-5"),
    "openai":    Provider("openai", "OPENAI_API_KEY", None,
                          "gpt-5.5", "gpt-4.1-mini",
                          catalog_url="https://api.openai.com/v1/models"),
    "openrouter": Provider("openai", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1",
                           "nvidia/nemotron-3-super-120b-a12b:free",
                           "google/gemma-4-26b-a4b-it:free"),
}

KEY_URLS = {
    "anthropic": "https://console.anthropic.com/settings/keys",
    "openai": "https://platform.openai.com/api-keys",
    "openrouter": "https://openrouter.ai/keys",
}


def _no_key_message(name: str, key_env: str) -> str:
    from paperclip.config import DOTENV_PATH

    where = (f"Add it to {DOTENV_PATH}:\n"
             f"    {key_env}=your-key-here"
             if DOTENV_PATH else
             f"No .env found from {os.getcwd()} upward — create one here:\n"
             f"    echo '{key_env}=your-key-here' >> .env")
    url = KEY_URLS.get(name)
    return (
        f"No API key for provider '{name}'.\n\n"
        f"  1. Get a key: {url}\n" if url else f"No API key for provider '{name}'.\n\n"
    ) + (
        f"  2. {where}\n\n"
        f"Other providers: {', '.join(sorted(PROVIDERS))}\n"
        f"Switch with PAPERCLIP_PROVIDER=<name> and that provider's key."
    )


def _families(provider: Provider) -> set[str]:
    names = (provider.model, provider.small_model, provider.flagship, provider.fast)
    return {n.split("-")[0].lower() for n in names if n and "/" not in n}


def _belongs_elsewhere(model: str, provider_name: str) -> bool:
    family = model.split("-")[0].lower()
    if "/" in model or not family:
        return False
    owner = {f: name for name, p in PROVIDERS.items() if "/" not in (p.model or "x")
             for f in _families(p)}.get(family)
    return bool(owner) and owner != provider_name


def get_client(settings: Settings):
    """Anthropic-shaped client: native Anthropic or OpenAICompatClient."""
    provider = PROVIDERS.get(settings.provider)
    if provider is None:
        raise SystemExit(f"Unknown PAPERCLIP_PROVIDER '{settings.provider}'. "
                         f"Pick one of: {', '.join(PROVIDERS)}")

    api_key = (settings.api_key or os.getenv(provider.key_env, "")).strip()
    if not api_key:
        raise SystemExit(_no_key_message(settings.provider, provider.key_env))
    try:
        api_key.encode("latin-1")
    except UnicodeEncodeError:
        raise SystemExit(
            f"{provider.key_env} contains a non-ASCII character (e.g. a smart quote "
            f"or arrow from a bad paste). Re-paste the key with no spaces or line breaks."
        )

    for attr in ("model", "small_model"):
        inherited = os.getenv(f"PAPERCLIP_{attr.upper()}", "").strip()
        if inherited and getattr(settings, attr, "") == inherited \
                and _belongs_elsewhere(inherited, settings.provider):
            setattr(settings, attr, "")

    settings.model = settings.model or provider.model
    settings.small_model = getattr(settings, "small_model", "") or provider.small_model
    base_url = settings.base_url or provider.configured_base_url()

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
                calls = []
                for b in content:
                    if getattr(b, "type", "") != "tool_use":
                        continue
                    call = {"id": b.id, "type": "function",
                            "function": {"name": b.name, "arguments": json.dumps(b.input)}}
                    extra = getattr(b, "extra", None)
                    if extra:
                        call["extra_content"] = extra
                    calls.append(call)
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
            m = str(exc).lower()
            if "max_completion_tokens" not in m and "max_tokens" not in m:
                raise
            k = dict(kwargs)
            k["max_tokens"] = k.pop("max_completion_tokens", None)
            return self._client.chat.completions.create(**k, **extra)

    def _create(self, *, model, messages, max_tokens, system=None, tools=None):
        response = self._call(self._to_openai(
            model=model, messages=messages, max_tokens=max_tokens, system=system, tools=tools))
        if not getattr(response, "choices", None):
            err = getattr(response, "error", None) or "endpoint returned no choices"
            raise RuntimeError(f"{model}: {err}")
        choice = response.choices[0].message
        blocks = []
        if choice.content:
            blocks.append(SimpleNamespace(type="text", text=choice.content))
        for call in choice.tool_calls or []:
            blocks.append(SimpleNamespace(
                type="tool_use", id=call.id, name=call.function.name,
                input=json.loads(call.function.arguments or "{}"),
                extra=getattr(call, "extra_content", None),
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
