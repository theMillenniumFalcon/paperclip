# Telegram gateway

Code: `paperclip/gateway/telegram.py`

Message your Paperclip from Telegram. **Long polling** — the laptop calls Telegram’s API; no public URL, no webhook.

Uses [`GatewayAgentRunner`](runner.md) (`session_id="telegram"`, `source="telegram"`) and [`run_gateway_turn`](runner.md). Tool/gate lines go to the laptop terminal via `cli._observer`.

## Setup

1. Telegram → @BotFather → `/newbot` → copy token.
2. `.env`: `TELEGRAM_BOT_TOKEN=...`
3. **Strongly recommended:** `TELEGRAM_ALLOWED_USER=<numeric id>` (from @userinfobot). Comma-separate for several users.  
   **Unset = anyone who finds the bot** can use your memory, tools, and API key. `posture()` prints which mode you’re in at startup.
4. Install extra: `pip install 'paperclip-agent[telegram]'` (or project’s `[telegram]` extra).
5. Run: `make telegram` or `python -m paperclip.gateway.telegram`.

Token is read via `load_settings().telegram_token` (typically backed by `TELEGRAM_BOT_TOKEN` in settings).

## Allowlist

`_allowed_ids()` parses `TELEGRAM_ALLOWED_USER` from the environment (comma-separated). `_build_app` may also accept a legacy `allowed` string argument; env is the source of truth.

Non-allowlisted users get: *"This Paperclip serves someone else. Run your own!"*

Handlers: text messages only (`TEXT`, not commands).

## Entry points

| Function | Role |
| --- | --- |
| `main()` | Standalone poller; exits if no token or missing extra; `runner.close()` in `finally` |
| `start_in_background()` | For `paperclip dashboard`: daemon thread + own asyncio loop. Returns `None` if no token or no extra (no raise). |
| `_build_app(token, allowed="", runner=None)` | Shared `Application` + handler for standalone and background |

## `TelegramHandle`

Returned by `start_in_background()`:

| Method | Behavior |
| --- | --- |
| `stop()` | Stop updater/app on the poller thread, join thread, `runner.close()` |
| `status()` | `IntegrationStatus` — see [Integrations](../integrations.md) |

Status rules:

- Another poller on same token → `ERROR` (“another instance is polling”)
- Thread died → `ERROR` (“gateway stopped unexpectedly”)
- `runner.error_status` set → `ERROR` with that message
- Else → `CONNECTED`

Background mode detects `telegram.error.Conflict` once and prints a plain hint (no traceback spam). PTB/httpx log levels are turned down on the dashboard path.

## Run

```bash
python -m paperclip.gateway.telegram
```

Or start with the dashboard when `TELEGRAM_BOT_TOKEN` is set.
