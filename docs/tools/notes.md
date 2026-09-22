# Notes tool

Code: `paperclip/tools/notes.py`

`save_note` — the **explicit** path into [semantic memory](../memory/semantic.md). The model calls it when the user asks to remember something (`remember that Alex prefers mornings`). The **implicit** path is [consolidation](../memory/consolidation.md), which distills facts from chat without a tool call.

## `make_tool(conn)`

Returns a `Tool` named `save_note`. `conn` is the same SQLite connection as `SqliteFactStore` (`facts` table).

| Argument | Meaning |
| --- | --- |
| `subject` | Who/what the fact is about (stored lowercased and stripped) |
| `content` | One-sentence fact |

Inserts `source='user'` (vs `'consolidation'` from the summarizer). Returns a confirmation string. Does not go through `SqliteFactStore.add`, but the SQL matches that helper.

Not wired into the loop in this checkout.
