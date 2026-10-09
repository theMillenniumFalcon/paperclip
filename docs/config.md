# Config

Code: `paperclip/config.py`

`load_dotenv()` runs at import (`.env` in the working directory). `load_settings()` returns a `Settings` dataclass. Empty model fields are filled later by `get_client` from the provider defaults.

`ensure_home()` creates `home`, `home/traces`, and `home/outbox`.

## Environment

| Field | Env | Default |
| --- | --- | --- |
| `provider` | `PAPERCLIP_PROVIDER` | `anthropic` |
| `api_key` | `PAPERCLIP_API_KEY` | empty (else the provider key env) |
| `base_url` | `PAPERCLIP_BASE_URL` | empty |
| `model` | `PAPERCLIP_MODEL` | empty |
| `small_model` | `PAPERCLIP_SMALL_MODEL` | empty (gate + consolidation) |
| `home` | `PAPERCLIP_HOME` | `.paperclip` |
| `max_iterations` | `PAPERCLIP_MAX_ITERATIONS` | `10` |
| `max_tokens` | `PAPERCLIP_MAX_TOKENS` | `2048` |
| `consolidate_every` | `PAPERCLIP_CONSOLIDATE_EVERY` | `6` |
| `retrieval_top_k` | `PAPERCLIP_RETRIEVAL_TOP_K` | `4` |
| `semantic_store` | `PAPERCLIP_SEMANTIC_STORE` | `sqlite` (`supabase` selects the vector store) |
| `apple_calendar` | `PAPERCLIP_APPLE_CALENDAR` | off unless value is `1`, `true`, or `yes` |
| `apple_tools` | `PAPERCLIP_APPLE_TOOLS` | same |
| `telegram_token` | `TELEGRAM_BOT_TOKEN` | empty |
| `otel_endpoint` | `OTEL_EXPORTER_OTLP_ENDPOINT` | empty (JSONL traces only) |

Providers: [loop models](loop/models.md).
