# Session

Code: `paperclip/runtime/session.py`

Working memory for one conversation. Rebuilt into the model call each turn. Persisted only when a `Memory` instance is attached (`log_chat` → `chat_log`).

```
system  = SOUL.md + local clock + (optional) gated memory + matching skills
history = prior user/assistant messages for this session_id
```

## `DEFAULT_SOUL` / `load_soul(settings)`

If `{home}/SOUL.md` is missing, write `DEFAULT_SOUL` and return it. Otherwise return the file as stored.

The default persona tells the model to use `create_event`, `list_events`, `save_note`, `send_message`, `github_read`, `manage_memory`, `update_soul`, and `create_skill`, to call each tool at most once per request, and to relay tool output about where artifacts landed (including `.paperclip/state.db`). `github_read` is read-only. Editing `SOUL.md` changes that persona on the next `load_soul`. An existing `SOUL.md` is not rewritten when the default text changes.

## `Session`

| Field | Meaning |
| --- | --- |
| `settings` | `Settings` |
| `memory` | `paperclip.memory.Memory` or `None` |
| `session_id` | Tag stored on `chat_log` rows (default `"default"`) |
| `history` | `[{role, content}, …]` for this conversation |

### `build_system(user_message, notify=None) -> str`

Joined with newlines:

1. Text from `load_soul`.
2. Local time: weekday, date, clock, timezone name, and UTC offset (`datetime.now().astimezone()`), so relative times can be resolved.
3. If `memory` is set:
   - `gated_retrieve(user_message, notify=notify)` — if non-empty, a “Relevant memory:” block ([retrieval gate](../memory/retrieval-gate.md)).
   - `matching_skills(user_message)` — if non-empty, “Relevant skill instructions:” ([procedural](../memory/procedural.md)).

### `add_exchange(user_message, reply, tool_calls=None, source="cli")`

Appends a user message and an assistant message to `history`.

If `tool_calls` is a list of `{tool, args, output}`, the assistant content is the reply plus one line:

`[tools used: tool(args) -> output; …]`

That line is what the model sees next turn, so it does not repeat the same call.

If `memory` is set, `log_chat(user_message, record, session_id, source)` stores the same assistant text (including the tools line).

### `start_new(session_id)`

Sets `session_id` and clears `history`. Older rows stay in `chat_log` under the previous id.

### `switch(session_id)`

Sets `session_id`, clears `history`, then if `memory` is set reloads every `(user, assistant)` pair from `memory.session_history(session_id)` in order.

Consolidation still reads all unconsolidated `chat_log` rows, not only the active session.
