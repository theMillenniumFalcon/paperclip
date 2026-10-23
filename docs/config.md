# Config

Code: `paperclip/config.py`

`load_env()` runs at import. It reads `{home}/.env`, then a `.env` in the working directory for keys the home file left blank (including blank `KEY=` lines). A variable already set in the process environment is left as-is. `load_settings()` calls `load_env()` again and returns a `Settings` dataclass. Empty model fields are filled later by `get_client` from the provider defaults.

The home folder is `PAPERCLIP_HOME` when that is set in the environment or in the working-directory `.env`. Otherwise it is `~/.paperclip` (on Windows, `%USERPROFILE%\.paperclip`). The first launch creates that folder and copies `.env.example` to `{home}/.env`. A later launch does not overwrite it. The installed wheel ships that example as `paperclip/env.example`; a source checkout reads the repo root `.env.example`.

`ensure_home()` creates `home`, `home/traces`, and `home/outbox`.

## Environment

| Field | Env | Default |
| --- | --- | --- |
| `provider` | `PAPERCLIP_PROVIDER` | `anthropic` |
| `api_key` | `PAPERCLIP_API_KEY` | empty (else the provider key env) |
| `base_url` | `PAPERCLIP_BASE_URL` | empty |
| `model` | `PAPERCLIP_MODEL` | empty |
| `small_model` | `PAPERCLIP_SMALL_MODEL` | empty (gate + consolidation) |
| `home` | `PAPERCLIP_HOME` | `~/.paperclip` |
| `max_iterations` | `PAPERCLIP_MAX_ITERATIONS` | `10` |
| `max_tokens` | `PAPERCLIP_MAX_TOKENS` | `2048` |
| `consolidate_every` | `PAPERCLIP_CONSOLIDATE_EVERY` | `6` |
| `retrieval_top_k` | `PAPERCLIP_RETRIEVAL_TOP_K` | `4` |
| `semantic_store` | `PAPERCLIP_SEMANTIC_STORE` | `sqlite` (`supabase` selects the vector store) |
| `apple_calendar` | `PAPERCLIP_APPLE_CALENDAR` | off unless value is `1`, `true`, or `yes` |
| `apple_tools` | `PAPERCLIP_APPLE_TOOLS` | same |
| `telegram_token` | `TELEGRAM_BOT_TOKEN` | empty |
| `otel_endpoint` | `OTEL_EXPORTER_OTLP_ENDPOINT` | empty (JSONL traces only) |
| `github_repo` | `PAPERCLIP_GITHUB_REPO` | empty (no default repo for `github_read`) |

Providers: [loop models](loop/models.md).
