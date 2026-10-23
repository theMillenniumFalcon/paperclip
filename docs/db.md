# SQLite state database

Code: `paperclip/db.py`

One file per install: `{home}/state.db` (default `~/.paperclip/state.db`). SQLite + FTS5, no separate server.

`connect(home, check_same_thread=True)` opens the file, runs `SCHEMA`, applies `_migrate`, sets `row_factory=sqlite3.Row`, `PRAGMA busy_timeout=3000`. Pass `check_same_thread=False` when a threaded server shares one connection (with a lock).

Inspect locally:

```bash
sqlite3 ~/.paperclip/state.db ".tables"
```

Memory stores use the same connection: [semantic](memory/semantic.md), [episodic](memory/episodic.md), [consolidation](memory/consolidation.md).

---

## Tables

### `calendar_events`

Local calendar rows (e.g. from a calendar tool). Evals can assert “did an event get created?”

| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY |
| `title` | TEXT | NOT NULL |
| `start` | TEXT | NOT NULL, ISO 8601 |
| `end` | TEXT | optional |
| `attendees` | TEXT | default `''`, comma-separated |
| `notes` | TEXT | default `''` |
| `created_at` | TEXT | default `datetime('now')` |

---

### `facts`

Semantic memory — durable facts.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY |
| `subject` | TEXT | NOT NULL, who/what (e.g. `alex`) |
| `content` | TEXT | NOT NULL |
| `source` | TEXT | default `'user'`; or `'consolidation'` |
| `created_at` | TEXT | default `datetime('now')` |

**`facts_fts`** — FTS5 virtual table on `subject`, `content`, backed by `facts` (`content_rowid=id`). Triggers `facts_ai`, `facts_ad`, `facts_au` keep the index in sync on insert/delete/update.

---

### `episodes`

Episodic memory — dated summaries.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY |
| `happened_at` | TEXT | NOT NULL, ISO 8601 date |
| `summary` | TEXT | NOT NULL |
| `created_at` | TEXT | default `datetime('now')` |

**`episodes_fts`** — FTS5 on `summary`, backed by `episodes`. Triggers `episodes_ai`, `episodes_ad` on insert/delete (no update trigger in schema).

---

### `chat_log`

Raw messages before/after consolidation. `consolidation.py` reads rows with `consolidated = 0`.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER | PRIMARY KEY |
| `role` | TEXT | NOT NULL, `'user'` or `'assistant'` |
| `content` | TEXT | NOT NULL |
| `consolidated` | INTEGER | default `0`; set to `1` after distill |
| `session_id` | TEXT | default `'default'`; groups a conversation |
| `created_at` | TEXT | default `datetime('now')` |

`session_id` is in the `CREATE TABLE`. Older databases get it from `_migrate` if the column is missing.

`source` is **not** in the `CREATE TABLE`. `_migrate` adds it when missing: `TEXT DEFAULT 'cli'` (cli, voice, telegram, dashboard, brief).

---

## `connect(home, check_same_thread=True)`

Opens `{home}/state.db`, `row_factory=sqlite3.Row`, `PRAGMA busy_timeout=3000`, runs `SCHEMA`, then `_migrate`. `check_same_thread=False` is for the dashboard’s shared connection (guarded by a lock).
