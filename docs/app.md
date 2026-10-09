# App

Code: `paperclip/app.py`

`Paperclip` is one running agent. Gateways call `respond()`.

## Constructor

`Paperclip(settings=None, client=None, conn=None)`

1. `settings` or `load_settings()`, then `ensure_home()`.
2. `conn` or `connect(home)`.
3. `client` or `get_client(settings)`.
4. `Memory`, then `build_registry` (tools that need memory).
5. `mcp_bridge` from the registry when `mcp.json` started servers.
6. `Session` with that memory, and a `Tracer`.

`client` and `conn` are injection points: evals pass a scripted client; the dashboard passes a connection with `check_same_thread=False`.

`close()` stops the MCP bridge if one was started.

## `respond(user_message, observer=None, source="cli", stream=False)`

1. Observer is `compose(observer, tracer.event)` so the gateway and the trace both see events.
2. Inside `tracer.turn`: build the system prompt, append the user message to a copy of session history, `run_loop` with `settings.model`, `max_iterations`, and `max_tokens`.
3. `session.add_exchange` (history + `chat_log`, tagged with `source`).
4. `maybe_consolidate`, then `export_markdown` (`MEMORY.md`).
5. `tracer.end_turn` and return the `LoopResult`.

`stream=True` asks the loop to emit text deltas to the observer (dashboard chat).
