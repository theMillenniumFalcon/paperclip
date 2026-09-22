# Semantic store

Code: `paperclip/memory/semantic/store.py`

Durable facts, searched with SQLite FTS5. Same database file as [episodes](episodic.md); different table and ranking.

Older comments mentioned `PAPERCLIP_SEMANTIC_STORE=supabase` and `supabase_store.py`. That file is not in this repo.

## `SqliteFactStore`

Holds a `sqlite3.Connection`.

| Method | Behavior |
| --- | --- |
| `add(subject, content, source="user")` | Insert; `subject` is lowercased and stripped. `source` is `"user"` or `"consolidation"`. |
| `search(query, top_k=4)` | FTS join `facts_fts` → `facts`, `ORDER BY rank`. Format `[subject] content`. Empty FTS query → `[]`. |
| `list(limit=200)` | Newest ids first, full dicts (dashboard). |
| `search_with_ids(query, top_k=8)` | Like search with ids; empty query → `list(top_k)`. |
| `update` / `delete` | Return whether a row was affected. FTS must stay in sync (typically via SQLite triggers on the schema). |
| `settle(timeout=120)` | Always `True`. Row and FTS index land in one transaction, so a fact is searchable as soon as `add()` returns. Hosted backends would need a real wait. |

## FTS5 query helper

`_fts_query(text)` is also used by `SqliteEpisodeStore.search`. User text is not a valid FTS5 `MATCH` string.

It:

1. **Lowercases** the text. FTS5 operators (`AND` / `OR` / `NOT` / `NEAR`) are uppercase only. Lowercasing stops `"Alex and Bob"` from becoming a boolean expression.
2. Tokenizes with `[^\W_]{2,}` — Unicode alphanumeric, **excluding underscore**. That matches unicode61 (underscore is a separator). `paper_clip` is two terms in the index and must be two terms in the query.

   An ASCII-only `[a-zA-Z0-9]` used to:
   - Truncate accented names (`Müller` → `ller`) → silent misses.
   - Drop non-Latin scripts to `""`. Empty query is **not** a no-op in episode search: it falls back to **recent** episodes, so a query about `Сергей` could inject unrelated English memory.

3. Dedupes tokens (order preserved) and joins with ` OR `.
4. **CJK / Japanese prefix:** if a token contains Hiragana, Katakana, or CJK ideographs, it becomes `token*`. unicode61 does not segment those scripts, so a whole run can be one indexed term and an exact name inside it never hits. Prefix is applied **only** to those tokens. Prefixing every token would make `car` match `carpet`.

If no tokens remain, returns `""`. Callers decide what that means: facts return no hits; episodes return recent.
