# Notes

Code: `paperclip/tools/notes.py`

## `save_note`

`make_tool(conn)`. Inserts into `facts` with `source='user'`. `subject` is lowercased and stripped.

This is the **explicit** “remember that …” path. Implicit facts still come from [consolidation](../memory/consolidation.md).

Returns `Saved to memory under '{subject}': {content}`.
