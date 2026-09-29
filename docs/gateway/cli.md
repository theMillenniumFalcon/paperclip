# CLI gateway

Code: `paperclip/gateway/cli.py`

Terminal chat with Paperclip: read a line, call `Paperclip.respond`, print the reply. Uses **Rich** for panels and dim tool/gate traces.

Depends on a full `Paperclip` instance (`session`, `conn`, `respond`, …). In a minimal checkout only eval wiring may exist; this module is the intended REPL once the app is assembled.

## Startup

- `Paperclip()` with default settings.
- `session.session_id = "terminal"` — separate thread in the unified inbox.
- Banner: home path, model id, commands `/memory` · `/quit`.

## Commands

| Input | Action |
| --- | --- |
| `/quit`, `/exit` | Leave the loop |
| `/memory` | Read-only snapshot from `state.db` via `paperclip.conn` |
| anything else | `respond(message, observer=_observer, source="cli")` |

Empty lines are skipped. `EOF` / Ctrl+C exits cleanly.

## `/memory` snapshot

`_memory_snapshot(conn)` — no writes:

- Count + latest 8 facts (`subject`, `content`)
- Count + latest 5 episodes (`happened_at`, `summary`)
- Count of `chat_log` rows with `consolidated = 0`

## `_observer`

Live harness output (dim):

| `kind` | Shows |
| --- | --- |
| `tool` | name, args, first 80 chars of output |
| `gate` | retrieval gate decision + reason |
| `consolidation` | how many facts were written |

## Run

```bash
python -m paperclip.gateway.cli
```

Requires `rich` if not already a project dependency.
