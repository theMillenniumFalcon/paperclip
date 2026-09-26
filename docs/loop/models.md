# Model access

Code: `paperclip/loop/models.py`

The rest of Paperclip speaks **one dialect**: Anthropic **Messages** (`system`, `messages`, `tools` in; content blocks + `stop_reason` out). Providers plug in as:

| Wire format | Providers |
| --- | --- |
| Native Anthropic | `anthropic` |
| OpenAI `chat.completions` (adapter) | `openai`, `openrouter` |

Env: `PAPERCLIP_PROVIDER`, provider key (`ANTHROPIC_API_KEY`, …), optional `PAPERCLIP_MODEL` / `PAPERCLIP_SMALL_MODEL`, `PAPERCLIP_BASE_URL`, `PAPERCLIP_LLM_TIMEOUT` (default 120s).

## `Provider` / `PROVIDERS`

Each entry defines:

| Field | Meaning |
| --- | --- |
| `kind` | `anthropic` or `openai` (adapter path) |
| `key_env` | Env var for the API key |
| `model` | Default **main** loop model |
| `small_model` | Default **cheap** model (retrieval gate, consolidation) |
| `flagship` / `fast` | UI switcher defaults (fallback to model / small_model) |
| `catalog_url` | Model list for Settings picker |
| `base_url_env` / `endpoints` | Optional regional endpoints + per-region catalogs |

Built-ins (defaults may change):

| Name | Main | Small |
| --- | --- | --- |
| `anthropic` | claude-sonnet-5 | claude-haiku-4-5-20251001 |
| `openai` | gpt-5.5 | gpt-4.1-mini |
| `openrouter` | nemotron … `:free` | gemma … `:free` |

OpenAI default avoids reasoning-only models that 400 on `chat.completions` without tool support. OpenRouter defaults use `:free` tier (rate-limited).

`KEY_URLS` — where to obtain keys (shown in missing-key errors with absolute `.env` path from `DOTENV_PATH`).

## `get_client(settings)`

1. Resolve `PROVIDERS[settings.provider]` or exit.
2. Load API key (`settings.api_key` or `key_env`), strip whitespace, validate latin-1 (bad paste → clear error).
3. **Model leak guard:** If `PAPERCLIP_MODEL` / `PAPERCLIP_SMALL_MODEL` in the environment still match `settings.model` / `settings.small_model` but the model **family** belongs to another provider (e.g. Anthropic haiku while provider is OpenAI), clear that field so provider defaults apply. Explicit non-env overrides are kept. Stops the retrieval gate from failing open every turn with “model not found.”
4. Fill empty `model` / `small_model` from provider defaults.
5. Return `anthropic.Anthropic(...)` or `OpenAICompatClient(...)`.

## `OpenAICompatClient`

Implements `.messages.create` and `.messages.stream` in Anthropic shape over OpenAI’s API.

**`_to_openai`** — Maps system string, user/assistant strings, assistant tool_use blocks, and tool_result dicts to OpenAI messages. Tools: Anthropic `input_schema` → OpenAI `parameters`. Carries `extra_content` on tool calls for Gemini **thought_signature** round-trip.

**`_call`** — `chat.completions.create`; if the error mentions `max_completion_tokens` vs `max_tokens`, retry with the other key name only for that error.

**`_create`** — Empty `choices` (e.g. OpenRouter rate limit body) → `RuntimeError` with body error. Else build text + `tool_use` blocks, map usage to `input_tokens` / `output_tokens`, `stop_reason` `tool_use` or `end_turn`.

**`_OpenAIStream`** — Context manager like Anthropic’s stream: iterate `text_stream`, then `get_final_message()` with reassembled tool calls and usage.
