# Memory admin tools

Code: `paperclip/tools/memory_admin.py`

Registered only when `build_registry(..., memory=...)` gets a `Memory` instance.

## `manage_memory`

| `action` | `kind` | Behavior |
| --- | --- | --- |
| `search` | `fact` (default) | `facts.search_with_ids(query, 8)` if the store has that method |
| `search` | `episode` | `episodes.list(20)`, optional substring filter on `summary`, first 8 |
| `update` | `fact` | `facts.update(id, content, subject or None)`. Episodes cannot be updated |
| `delete` | `fact` or `episode` | `delete(id)` |

Unknown action → message listing `search`, `update`, `delete`.

## `update_soul`

Appends one bullet under `## Learned rules` in `{home}/SOUL.md`. Uses `load_soul` from `paperclip/runtime/session.py` (creates the file from the default persona if missing). Strips a leading `-`. Refuses when the file is longer than `SOUL_MAX` (8000). Append-only.

## `create_skill`

Slug: lowercase, spaces → hyphens, must match `^[a-z0-9][a-z0-9-]{1,40}$`.

Writes `{home}/skills/<name>/SKILL.md`. Refuses if that path or repo `skills/<name>/SKILL.md` already exists. Validates with `_parse_text`. Calls `memory.skills.refresh()` so the skill can match on the next turn.
