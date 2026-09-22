# Episodic store

Dated events: what happened, and when. Semantic memory is “what I know”; this is “what happened last Tuesday.”

Two backends share roughly the same methods. Consolidation is typed against SQLite only.

## SQLite — `SqliteEpisodeStore`

Code: `paperclip/memory/episodic/store.py`

Same SQLite file as facts. Retrieval is **FTS for relevance**, then **`happened_at` descending** among matches.

| Method | Behavior |
| --- | --- |
| `add(summary, happened_at)` | Insert date + summary. |
| `search(query, top_k=3)` | Sanitize with `_fts_query`. Empty → `recent()`. Else `episodes_fts MATCH`, `ORDER BY rank, e.happened_at DESC`. Format `(YYYY-MM-DD) summary`. |
| `recent(top_k=3)` | `ORDER BY happened_at DESC` (not `created_at`). |
| `list(limit=200)` | Newest ids first, full dicts. |
| `delete(episode_id)` | SQL `DELETE`; returns whether a row was removed. |

Query sanitization: [semantic store](semantic.md#fts5-query-helper). Empty FTS query falling back to `recent()` is why a broken tokenizer (all tokens dropped) is dangerous: the model still gets “relevant memory,” just the wrong events.

## Notion — `NotionEpisodeStore`

Code: `paperclip/memory/episodic/notion_store.py`

Episodes as Notion pages a human can read. Facts stay in SQLite.

### Setup

- `NOTION_TOKEN` and `NOTION_EPISODES_DATABASE_ID` (or constructor `token=` / `database_id=`).
- Database properties: **Name** (title = `happened_at` string) and **Summary** (rich text).
- Notion API 2025-09-03 / `notion-client` ≥ 2.5: rows live under a **data source**. The constructor retrieves the database, takes `data_sources[0].id`, then creates/queries via that id.

`normalize_database_id` accepts a raw id or a copied Notion URL. The 32-hex **database** id is in the path; `v=` is a view id.

### How it differs from SQLite

| Method | Notion |
| --- | --- |
| `add` | Creates a page under the data source. |
| `recent` / `search` / `list` | Fetches **all** pages (paginated), then filters/sorts in Python. |
| `search` | Not Notion’s search API. Word-boundary match on alphanumeric keywords in the summary; empty keywords → `recent`. No FTS/BM25. |
| `delete` | **Archives** the page. Always returns `True`. Ids are Notion page UUIDs (`int \| str`). |

Fine for a personal database; not for huge logs. Search is O(all episodes) every call.
