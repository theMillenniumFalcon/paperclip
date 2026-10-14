# Dashboard

Code: `paperclip/ops/dashboard.py`

Stdlib `ThreadingHTTPServer` bound to **127.0.0.1**. A JSON API (plus one SSE stream) over the same home directory the agent uses (`PAPERCLIP_HOME`, default `.paperclip`). It serves **no frontend**: the UI is a separate Next.js app that calls this API from another origin.

## Run

```bash
python -m paperclip.ops.dashboard
```

Port: `PAPERCLIP_DASHBOARD_PORT`, else `PORT`, else `7777`. If that port is busy, the next ports up to +9 are tried, so the frontend's API base URL must be configurable. Startup prints `Paperclip API -> http://localhost:<port>`. If `TELEGRAM_BOT_TOKEN` is set, `start_in_background()` from the Telegram gateway is started on a daemon thread.

## CORS

The Next.js app runs on a different origin, so the server sends CORS headers, but only for allowlisted origins (never `*`). This matters because `/api/settings` writes API keys and `/api/reveal` opens files on the host.

| Item | Behavior |
| --- | --- |
| `PAPERCLIP_DASHBOARD_ORIGINS` | Comma-separated allowlist. Default: `http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001` |
| Matching origin | Response gets `Access-Control-Allow-Origin` (echoing the origin), `Vary: Origin`, `Allow-Methods: GET, POST, OPTIONS`, `Allow-Headers: Content-Type` |
| Other origins | No CORS headers, so the browser blocks the call |
| `OPTIONS` (any path) | `204` preflight response with the same CORS headers |

CORS headers are also sent on the `/api/chat/stream` SSE response. If the frontend runs on another port or host, set `PAPERCLIP_DASHBOARD_ORIGINS` or every request will be blocked.

## Frontend

There are no static files. The old `/static/<file>` route and the `index.html` fallback were removed along with `STATIC`. The cockpit UI (overview, turns, memory, tools, database, evals, spend, settings, chat dock) lives in the Next.js app under `dashboard/`.

```bash
cd dashboard
bun run dev
```

The app calls `NEXT_PUBLIC_PAPERCLIP_API` (default `http://127.0.0.1:7777`). Its browser origin must be listed in `PAPERCLIP_DASHBOARD_ORIGINS`.

- Any path that is not a known route returns `404` with `{"error": "not found"}` (GET and POST).
- `/api/chat/stream` is a **POST** with an SSE response body, so the browser `EventSource` cannot be used. Read it with `fetch` and a stream reader.
- Call the stream endpoint directly, not through a Next.js rewrite, because the proxy can buffer streamed responses.

## Agent

`_get_agent()` builds one shared `Paperclip(settings=..., conn=...)` on first chat. `conn` is `connect(home, check_same_thread=False)`. A lock serializes turns. Settings changes rebuild it and call `close()` on the previous instance.

## GET

| Path | Returns |
| --- | --- |
| `/api/data` | `collect()` — one blob for the whole page (see below) |
| `/api/events?cursor=` | New lines in today’s `traces/YYYY-MM-DD.jsonl` after `cursor`. `cursor` omitted → empty events and the current line count |
| `/api/reveal?path=` | Opens a path under home (or a repo skill path) in `PAPERCLIP_EDITOR`, else `cursor`, else `code`, else the OS file browser |
| anything else | `404` `{"error": "not found"}` |

## POST

| Path | Body | Behavior |
| --- | --- | --- |
| `/api/chat` | `{message}` | One `respond(..., source="dashboard")`. JSON: reply, gate, tools, consolidation, iterations, latency |
| `/api/chat/stream` | `{message}` | SSE `data:` events as the turn runs, then `kind: done` |
| `/api/voice` | raw audio bytes | faster-whisper (`PAPERCLIP_WHISPER_MODEL`, default `base`) → `{text}` |
| `/api/memory` | action payload | Update/delete facts or episodes, rewrite `SOUL.md`, or save a `SKILL.md` inside the skills folders |
| `/api/settings` | provider, model, small_model, keys | Writes `.env` keys listed below and rebuilds the agent |
| `/api/query` | `{sql}` | One read-only `SELECT` or `WITH` against `state.db`, max 200 rows |
| `/api/session` | `{action, id?}` | `new`, `switch`, or `history` on `chat_log` |
| anything else | — | `404` `{"error": "not found"}` |

Settings keys that may be written: `PAPERCLIP_PROVIDER`, `PAPERCLIP_MODEL`, `PAPERCLIP_SMALL_MODEL`, `TAVILY_API_KEY`, and each provider’s `key_env`. Empty key values are not written. Keys in the API response are last-4 only.

## `collect()`

Reads traces, `state.db`, skills, outbox, eval files, and `usage.jsonl`.

| Field | Contents |
| --- | --- |
| `stats` | Turn count, tool calls/errors, gate skip/retrieve, tokens, estimated cost, latency avg and p95 |
| `turns` | Last 50 turns (user text, gate, llm calls, tools, reply). Unfinished turns are marked |
| `wake_scans` | Last 25 voice wake near-misses |
| `trace_tail` | Last 18 raw trace lines |
| `facts`, `episodes`, `chat_log`, `chat_pending` | Memory tables; pending is `consolidated = 0` |
| `sessions`, `current_session` | Conversation picker |
| `soul`, `skills` | `SOUL.md` and loaded `SKILL.md` files |
| `calendar`, `outbox` | Local events and the newest 20 outbox drafts |
| `eval_report`, `eval_history` | Latest verdict and last 20 lines of `eval_runs.jsonl` |
| `db` | Path, size, and samples of `calendar_events`, `facts`, `episodes`, `chat_log` |
| `settings` | Provider, models, which keys are set |
| `tools` | Live registry if an agent exists; otherwise a display catalog (MCP servers are not started just to render) |
| `usage` | All-time tokens and estimated dollars from `usage.jsonl` |

Cost uses approximate per-provider dollars per million tokens and is labelled as an estimate. Tool lines are `ok`, `warn`, or `error` from the output text (`failed` / `error` / `timed out` → error; `already exists`, `not synced`, `skipped` → warn).