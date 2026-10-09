# Model access

Code: `paperclip/loop/models.py`

Paperclip speaks one dialect: Anthropic **Messages** (`system`, `messages`, `tools` in; content blocks + `stop_reason` out). Three providers:

| `PAPERCLIP_PROVIDER` | Wire | API key env | Default base URL |
| --- | --- | --- | --- |
| `anthropic` | Native Anthropic SDK | `ANTHROPIC_API_KEY` | (default) |
| `openai` | OpenAI adapter | `OPENAI_API_KEY` | (default) |
| `openrouter` | OpenAI adapter | `OPENROUTER_API_KEY` | `https://openrouter.ai/api/v1` |

Also: `PAPERCLIP_API_KEY` (optional override for the active provider’s key), `PAPERCLIP_MODEL`, `PAPERCLIP_SMALL_MODEL`, `PAPERCLIP_BASE_URL` (overrides provider default URL), `PAPERCLIP_LLM_TIMEOUT` (seconds, default `120`).

## `Provider` / `PROVIDERS`

| Field | Meaning |
| --- | --- |
| `kind` | `anthropic` → `anthropic.Anthropic`; `openai` → `OpenAICompatClient` |
| `key_env` | Env var for the API key when `PAPERCLIP_API_KEY` is empty |
| `base_url` | Default OpenAI-compatible base (OpenRouter only unless overridden) |
| `model` | Default main loop model |
| `small_model` | Default cheap model (retrieval gate, consolidation) |

Default model ids (override with env or `Settings`):

| Provider | Main | Small |
| --- | --- | --- |
| `anthropic` | `claude-sonnet-5` | `claude-haiku-4-5-20251001` |
| `openai` | `gpt-5.5` | `gpt-4.1-mini` |
| `openrouter` | `nvidia/nemotron-nano-9b-v2:free` | `google/gemma-3-4b-it:free` |

OpenAI defaults avoid reasoning-only models that reject `chat.completions` without tools. OpenRouter defaults use `:free` tiers (rate-limited).

## `get_client(settings)`

1. Look up `PROVIDERS[settings.provider]` or exit with allowed names.
2. API key: `settings.api_key` or `provider.key_env` from the environment; exit if missing.
3. Fill empty `settings.model` / `settings.small_model` from the provider row.
4. `base_url` = `settings.base_url` or `provider.base_url`.
5. Return `anthropic.Anthropic(...)` or `OpenAICompatClient(...)`.

Hung network calls use `PAPERCLIP_LLM_TIMEOUT` on the client.

## `OpenAICompatClient`

Exposes `.messages.create` and `.messages.stream` in Anthropic shape over OpenAI `chat.completions`.

**`_to_openai`** — Maps system, user/assistant strings, assistant `tool_use` blocks, and `tool_result` dicts to OpenAI messages. Tool schemas: Anthropic `input_schema` → OpenAI `parameters`.

**`_call`** — `chat.completions.create`; on failure, retries with `max_tokens` instead of `max_completion_tokens`.

**`_create`** — Builds text + `tool_use` blocks, maps usage to `input_tokens` / `output_tokens`, sets `stop_reason` to `tool_use` or `end_turn`.

**`_OpenAIStream`** — Context manager: iterate `text_stream`, then `get_final_message()` with reassembled tool calls and usage.
