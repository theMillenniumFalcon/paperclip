# Semantic store

Code: `paperclip/memory/semantic/store.py` (default), `semantic/supabase_store.py` (optional).

Durable **facts**, searched for injection into the prompt. Episodes use the same FTS helper: `_fts_query` in `store.py`.

## `SqliteFactStore`

Holds a `sqlite3.Connection` to `state.db`.

| Method | Behavior |
| --- | --- |
| `add(subject, content, source="user")` | Insert; `subject` lowercased/stripped. `source` e.g. `user`, `consolidation`. |
| `search(query, top_k=4)` | `facts_fts MATCH` → `ORDER BY rank`. Lines `[subject] content`. Empty FTS → `[]`. |
| `list(limit=200)` | Newest ids first. |
| `search_with_ids(query, top_k=8)` | Like search with ids; empty query → `list(top_k)`. |
| `update` / `delete` | Return whether a row changed. FTS sync via DB triggers (see [db.md](../db.md)). |

Select backend with `PAPERCLIP_SEMANTIC_STORE=sqlite` (default).

## FTS query helper — `_fts_query(text)`

Shared with `SqliteEpisodeStore.search`.

1. Lowercase input.
2. Tokens: `[a-zA-Z0-9]{2,}` (ASCII alphanumeric, length ≥ 2).
3. Dedupe preserving order; join with ` OR ` for FTS5 `MATCH`.

If no tokens, returns `""`. **Facts:** no hits. **Episodes:** empty query falls back to `recent()` — see [episodic.md](episodic.md).

## Supabase — `SupabaseFactStore`

Code: `paperclip/memory/semantic/supabase_store.py`

Same `add` / `search` surface as SQLite facts, but storage is Supabase `rag_chunks` + `match_chunks` RPC (pgvector). Embeddings via OpenAI `text-embedding-3-small` by default (`OPENAI_EMBED_MODEL` override).

Enable:

```bash
pip install 'paperclip[supabase]'   # supabase client + deps as defined in project extras
PAPERCLIP_SEMANTIC_STORE=supabase
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
OPENAI_API_KEY=...   # embeddings only
```

`Memory._make_fact_store` chooses this when `settings.semantic_store == "supabase"`.

| Method | Behavior |
| --- | --- |
| `add` | Upsert row with `chunk_id`, `source`=subject, `text`, `embedding` of `subject: content` |
| `search` | RPC `match_chunks` with query embedding; same `[source] text` format |

Use when phrasing diverges from stored wording; for hundreds of personal facts FTS is usually enough.
