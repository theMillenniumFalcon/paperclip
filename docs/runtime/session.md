# Session

Code: `paperclip/runtime/session.py`

**Ephemeral agent run** — rebuilt each turn for the model. Persists only when `memory` is attached (`log_chat` → `chat_log`).

```
system prompt  = SOUL.md + clock + model info + (optional) gated memory + skills
messages       = recent history + new user message   # windowed again in respond()
```

## `DEFAULT_SOUL` / `load_soul(settings)`

On first use, writes `{home}/SOUL.md` from `DEFAULT_SOUL` if missing. That file is the editable persona (tools, honesty about where artifacts live, one tool call per request, etc.). `load_soul` returns its text.

## `Session`

| Field | Meaning |
| --- | --- |
| `settings` | `Settings` (home, model, provider, …) |
| `memory` | `paperclip.memory.Memory` or `None` |
| `session_id` | Tag for `chat_log` rows (default `'default'`) |
| `history` | In-memory `[{role, content}, …]` for this conversation |

### `build_system(user_message, notify=None) -> str`

Pieces joined with newlines:

1. **SOUL** from `load_soul`.
2. **Local now** — weekday, date, time, timezone (for “next Tuesday”, “in 30 minutes”).
3. **Model line** — `settings.model`, `settings.provider`, Paperclip repo link.
4. If `memory` is set:
   - `memory.gated_retrieve(user_message, notify=notify)` → append “Relevant memory:” block if non-empty ([retrieval gate](../memory/retrieval-gate.md)).
   - `memory.matching_skills(user_message)` → append skill bodies if any ([procedural](../memory/procedural.md)).

### `add_exchange(user_message, reply, tool_calls=None, source="cli", meta=None)`

Appends user + assistant to `history`. If `tool_calls` is set, the assistant content includes a trailing  
`[tools used: tool(args) -> output; …]`  
so the model does not repeat the same tool next turn.

If `memory` is set, calls `memory.log_chat(..., session_id, source, meta)` for consolidation.

### `start_new(session_id)`

New conversation: set `session_id`, clear `history`. Rows in DB keep their old `session_id`; new messages use the new id.

### `switch(session_id)`

Load a past conversation: set id, clear history, then refill from `memory.session_history(session_id)` — last `settings.history_turns` exchanges only (requires `history_turns` on `Settings` when wired). No-op history reload if `memory` is `None`.

Consolidation still processes **all** unconsolidated `chat_log` rows, not per session.
