# Episodic store

Code: `paperclip/memory/episodic/store.py`

Dated **events**: what happened, and when. Semantic memory is “what I know”; episodic is “what happened on a given day.”

## `SqliteEpisodeStore`

Same SQLite file as facts. Search: **FTS relevance**, then **`happened_at` DESC** among matches.

| Method | Behavior |
| --- | --- |
| `add(summary, happened_at)` | Insert ISO date string + summary. |
| `search(query, top_k=3)` | `_fts_query` from [semantic store](semantic.md). Empty FTS → `recent(top_k)`. Else `episodes_fts MATCH`, `ORDER BY rank, e.happened_at DESC`. Format `(date) summary`. |
| `recent(top_k=3)` | `ORDER BY happened_at DESC`. |
| `list(limit=200)` | Newest ids first. |
| `delete(episode_id)` | SQL delete; returns whether a row was removed. |

Consolidation writes one episode per batch with `happened_at=date.today()` (see [consolidation.md](consolidation.md)).
