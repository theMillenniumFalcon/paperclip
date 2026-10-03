# WhatsApp gateway

Code: `paperclip/gateway/whatsapp.py`

WhatsApp via **Meta Cloud API** and an **HTTPS webhook** on port **5000** (`/webhook`). Unlike Telegram (long polling), Meta must reach your machine — you need a public URL (e.g. [ngrok](https://ngrok.com)) pointing at `https://<host>/webhook`.

Uses a **single `Paperclip`** instance inside the HTTP handler (not [`GatewayAgentRunner`](runner.md)): `ThreadingHTTPServer` + `threading.Lock` serializes turns; SQLite uses `connect(..., check_same_thread=False)`. `session_id="whatsapp"`, `source="whatsapp"`, `cli._observer` on the laptop.

## Setup (summary)

1. [Meta Developers](https://developers.facebook.com) — app with **WhatsApp** product; note **Phone Number ID**.
2. **Access token** (`WHATSAPP_TOKEN`) — temporary (24h) from Getting Started; prefer a permanent **System User** token for production.
3. **App Secret** (`WHATSAPP_APP_SECRET`) — Settings → Basic; used to verify `X-Hub-Signature-256` on POSTs.
4. **Verify token** (`WHATSAPP_VERIFY_TOKEN`) — any string you enter in Meta’s webhook config.
5. Expose port 5000: `ngrok http 5000` → set Callback URL to `https://…/webhook`, subscribe to **messages**.
6. `.env` + extra: `pip install 'paperclip-agent[whatsapp]'` (needs `httpx`).
7. `make whatsapp` or `python -m paperclip.gateway.whatsapp`.

**Sandbox:** Free tier usually only messages **test numbers** you add in the dashboard until business verification. **24h reply window** for normal messages; outside that, template messages only. **ngrok free URLs change** on restart — update Meta webhook each time.

## Environment

| Variable | Role |
| --- | --- |
| `WHATSAPP_TOKEN` | Bearer token for Graph API (`settings.whatsapp_token`) |
| `WHATSAPP_PHONE_NUMBER_ID` | Sender id for outbound API |
| `WHATSAPP_VERIFY_TOKEN` | Must match Meta’s GET verification query |
| `WHATSAPP_APP_SECRET` | HMAC webhook signature verification |
| `WHATSAPP_ALLOWED_PHONE` | Optional. If set, only this sender (no `+`, e.g. `15551234567`) is answered |

## HTTP handler

| Route | Behavior |
| --- | --- |
| `GET /webhook` | Meta subscribe challenge: `hub.mode=subscribe`, matching `hub.verify_token`, return `hub.challenge` |
| `POST /webhook` | Verify `X-Hub-Signature-256` with app secret; respond **200 immediately** (Meta retries on slow handlers); then parse `entry` → `changes` → `messages` |

For each text message: log, `paperclip.respond` under lock, `_send_message` reply via Graph API `v21.0/{phone_number_id}/messages`.

Invalid signature → 403. Wrong path → 404.

## Entry points

| Function | Role |
| --- | --- |
| `main()` | `ThreadingHTTPServer` on `0.0.0.0:5000`; exits if token/phone id/verify/app secret missing |
| `start_in_background()` | Daemon thread for dashboard; `None` if config incomplete or no extra; **raises** if port bind fails |

## `WhatsAppHandle`

| Method | Behavior |
| --- | --- |
| `stop()` | `server.shutdown()` from non-server thread, join |
| `status()` | Thread alive → `CONNECTED`; else `ERROR` |

No `runner.error_status` — errors are printed at send/respond time.

## Meta gotchas (detail)

- Temporary tokens expire in ~24 hours.
- Business verification + use-case approval are separate and slow.
- Rate limits (~80 msg/s on free tier); 429s possible.
- Phone numbers in webhooks omit `+` prefix.

Full step-by-step and pain points were in the old module docstring; this file is the canonical reference.

## Run

```bash
python -m paperclip.gateway.whatsapp
```

Webhook URL shown at startup: `http://<your-public-url>/webhook` (must be HTTPS for Meta).
