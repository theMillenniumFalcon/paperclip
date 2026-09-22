# Tool registry

Code: `paperclip/tools/registry.py`

## `Tool`

| Field | Meaning |
| --- | --- |
| `name` | What the model calls |
| `description` | Shown to the model so it knows when to use the tool |
| `input_schema` | JSON Schema for arguments (Anthropic `input_schema` shape) |
| `fn` | Python callable; must return a `str` |
| `wants_notify` | If true, `fn` also receives `_notify(kind, event)` (dashboard/live UI). Default no-op if the caller passes no notifier |

`to_api()` is the wire payload: `name`, `description`, `input_schema` only — not the function.

## `ToolRegistry`

| Method | Behavior |
| --- | --- |
| `register(tool)` | Store by `tool.name` (later register overwrites) |
| `schemas()` | `to_api()` for every tool, for `messages.create(..., tools=...)` |
| `execute(name, args, notify=None)` | Look up, call `fn(**args)` (and `_notify` if `wants_notify`) |

Unknown name or an exception inside `fn` becomes an **error string**, not a raised exception, so a bad tool call does not kill the turn.
