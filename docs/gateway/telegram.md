# Telegram gateway

Code: `paperclip/gateway/telegram.py`

Message Paperclip from Telegram. **Long polling**: this machine calls Telegram’s API; no public URL or webhook.

One `Paperclip` per built app (`session_id="telegram"`). Laptop logs `you ›` / `paperclip ›`; users get the reply in Telegram. Harness lines use [`cli._observer`](cli.md).

## Setup

1. Telegram → @BotFather → `/newbot` → copy token.
2. `.env`: `TELEGRAM_BOT_TOKEN=...` (loaded as `load_settings().telegram_token`).
3. **Recommended:** `TELEGRAM_ALLOWED_USER=<numeric id>` from @userinfobot. If set, only that user id is served; others get *"This Paperclip serves someone else. Run your own!"* If **unset**, anyone who finds the bot can use your agent.
4. `python -m paperclip.gateway.telegram` (or project `make telegram`).

Missing `python-telegram-bot`: exit message suggests `pip install 'paperclip[telegram]'`.

## `_build_app(token, allowed)`

Builds a `python-telegram-bot` `Application`:

- Creates `Paperclip()`, `session_id="telegram"`.
- **Handler** (async): if `allowed` is non-empty and `update.effective_user.id` does not match → deny message; else log text, `respond(..., source="telegram")`, `reply_text` with reply or `"(no reply)"`.
- Registers `MessageHandler(filters.TEXT & ~filters.COMMAND, handle)` — plain text only, not commands.

`allowed` is the raw string from `TELEGRAM_ALLOWED_USER` (single id in practice).

## `main()`

1. Import-check `telegram`; load token; exit with instructions if missing.
2. `_build_app(token, os.getenv("TELEGRAM_ALLOWED_USER", ""))`.
3. `app.run_polling()` (blocking).

## `start_in_background() -> bool`

For `paperclip api`: run Telegram on a **daemon thread** with its **own asyncio loop**. Must not crash the API.

| Condition | Return |
| --- | --- |
| No token | `False` |
| `telegram` import fails | `False` (prints install hint) |
| Otherwise | `True` after starting thread |

Thread body (`run`):

- Set `telegram` and `httpx` loggers to CRITICAL / WARNING so the dashboard terminal stays quiet.
- New event loop → `initialize` → `start` → `updater.start_polling(error_callback=on_poll_error)` → `run_forever`.
- Any other exception: print `(telegram) background poller stopped: …` (no re-raise).

**`on_poll_error`:** On `telegram.error.Conflict` (second poller on same token), print a **one-time** hint to stop the other `paperclip telegram` instance. Avoids traceback spam.

Thread name: `telegram-poll`.

## Run

```bash
python -m paperclip.gateway.telegram
```

Dashboard may call `start_in_background()` when `TELEGRAM_BOT_TOKEN` is set.
