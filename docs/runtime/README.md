# Runtime

Code: `paperclip/runtime/`

Per-turn **working memory**: the system prompt and the in-memory chat history for one conversation. Durable facts, episodes, and the chat log live in [memory](../memory/README.md) and [state.db](../db.md).

| Path | Doc | Role |
| --- | --- | --- |
| `session.py` | [session.md](session.md) | `load_soul`, `Session` |

`memory` on `Session` is optional. Without it, the prompt is persona plus the clock, and history stays in process only.

## Pages

- [Session](session.md)
