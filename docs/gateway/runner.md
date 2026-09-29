# Gateway runner

Code: `paperclip/gateway/runner.py`

Bridges **async** gateways (Telegram, Discord, …) to a **sync** `Paperclip` that owns SQLite. One dedicated worker thread per gateway: the event loop stays free, turns are serialized, and the DB connection is opened, used, and closed on that same thread.

## `safe_exception(exc) -> str`

Short error string for logs. Replaces env values whose names end with `_API_KEY`, `_TOKEN`, `_SECRET`, or `_PASSWORD` (length ≥ 4) with `***`, then caps at 500 chars.

## `GATEWAY_ERROR_REPLY`

Generic user-facing line when a turn fails: *"Paperclip couldn't process that message. Check the dashboard terminal."*

## `GatewayAgentRunner`

| Constructor arg | Role |
| --- | --- |
| `agent_factory` | Callable that builds a fresh `Paperclip` (lazy on first message) |
| `session_id` | Set on `agent.session.session_id` before the first turn |
| `source` | Passed to `respond(..., source=...)` (e.g. `telegram`) |
| `observer` | Optional `(kind, event)` callback (tools, gate, consolidation) |

**`async respond(text)`** — `run_in_executor` → `_respond` on the worker. Lazy-creates agent, calls `respond`, clears `error_status` on success.

**`error_status`** — Last short status after `record_error` (no secrets).

**`close()`** — Marks closed, runs `_close_agent` on the worker (`agent.close()`, closes `conn` if present), shuts down the executor (15s timeout on close).

After `close()`, `respond` raises `RuntimeError`.

## `run_gateway_turn(runner, text, send, logger=print)`

One end-to-end message:

1. Log `you › {text}`.
2. `await runner.respond(text)` — on failure, log redacted detail, `await send(GATEWAY_ERROR_REPLY)`, return `None`.
3. Log `paperclip › {reply}`.
4. `await send(result.reply or "(no reply)")` — on send failure, `record_error`, log, return `None`.
5. On success, `clear_error()` and return `result`.

`send` must be an async callable (e.g. post to Telegram). Delivery errors are separate from model errors.

## vs CLI

[`cli.py`](cli.md) runs `respond` on the main thread in a blocking loop. Runners use this module when the transport is async.
