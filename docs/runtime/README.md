# Runtime

Code: `paperclip/runtime/`

Per-turn **working memory**: what goes into the system prompt and the in-memory chat history for one conversation. Durable state lives in [memory](../memory/README.md) and [state.db](../db.md).

| Path | Role |
| --- | --- |
| `session.py` | `Session` — build system prompt, history, session switch |

Not fully wired in minimal `app.py` yet (`Memory` is optional on `Session`).

## Pages

- [Session](session.md)
