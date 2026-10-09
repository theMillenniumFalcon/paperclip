# Memory

Code: `paperclip/memory/`

Local memory for one assistant: **facts**, **dated episodes**, **skills**, a retrieval **gate**, and **consolidation** from `chat_log`. Docs are the reference for each module (one-line docstrings point here).

Not the hosted [Paperclip Memory](https://paperclip.pages.dev) MCP product — that store does not sync with `state.db`.

## Layout

| Path | Doc | Role |
| --- | --- | --- |
| `__init__.py` | (this page, `Memory`) | Facade wiring stores + gate + consolidation |
| `retrieval_gate.py` | [retrieval-gate.md](retrieval-gate.md) | Cheap LLM: search memory this turn? |
| `consolidation.py` | [consolidation.md](consolidation.md) | Cheap LLM: after N exchanges → facts + episode |
| `semantic/store.py` | [semantic.md](semantic.md) | SQLite facts + FTS5 |
| `semantic/supabase_store.py` | [semantic.md#supabase](semantic.md#supabase) | Optional vector backend |
| `episodic/store.py` | [episodic.md](episodic.md) | SQLite episodes + FTS |
| `procedural/loader.py` | [procedural.md](procedural.md) | `SKILL.md` match |
| `procedural/installer.py` | [procedural.md](procedural.md) | Install remote skill |

Schema: [Database](../db.md) (`facts`, `episodes`, `chat_log`, FTS tables).

## Three stores

| Kind | Question | Store |
| --- | --- | --- |
| Semantic | What do I know? | `SqliteFactStore` or `SupabaseFactStore` |
| Episodic | What happened, when? | `SqliteEpisodeStore` |
| Procedural | How should I act? | `SkillLoader` (`SKILL.md`) |

Default search is **FTS5 / BM25** on SQLite (no embeddings unless Supabase backend).

## Settings (`paperclip/config.py`)

| Env | Default | Used for |
| --- | --- | --- |
| `PAPERCLIP_HOME` | `.paperclip` | `MEMORY.md`, `skills/`, `state.db` |
| `PAPERCLIP_SMALL_MODEL` | (provider default) | Gate + consolidation |
| `PAPERCLIP_SEMANTIC_STORE` | `sqlite` | `supabase` → `SupabaseFactStore` |
| `PAPERCLIP_RETRIEVAL_TOP_K` | `4` | Fact search top-k |
| `PAPERCLIP_CONSOLIDATE_EVERY` | `5` | Exchanges before consolidation (`×2` chat_log rows) |

Supabase also needs `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, and `OPENAI_API_KEY` (embeddings). See [semantic.md#supabase](semantic.md#supabase).

## `Memory` facade

Constructed with `(conn, settings, client)` where `client` is Anthropic-shaped (`get_client`).

| Method | Behavior |
| --- | --- |
| `gated_retrieve(message, notify?)` | `should_retrieve` → if yes, `facts.search` + `episodes.search`; optional `notify("gate", …)` |
| `matching_skills(message)` | `SkillLoader.match` → markdown sections for the prompt |
| `log_chat(user, reply, session_id, source)` | Two `chat_log` rows, commit |
| `session_history(session_id)` | `(user, assistant)` pairs in order |
| `list_sessions()` | Per `session_id`: title, counts, timestamps |
| `export_markdown()` | Write `PAPERCLIP_HOME/MEMORY.md` from SQL |
| `maybe_consolidate(notify?)` | `consolidate_if_due`; optional `notify("consolidation", …)` |

Skill dirs: repo `skills/` and `{home}/skills`.

## Turn flow

```
User message
  → gated_retrieve()     # gate LLM → maybe FTS search
  → matching_skills()    # optional procedural injection
  → (agent responds)
  → log_chat()
  → maybe_consolidate()
  → export_markdown()    # if wired by the app
```

## Pages

- [Retrieval gate](retrieval-gate.md)
- [Consolidation](consolidation.md)
- [Semantic store](semantic.md)
- [Episodic store](episodic.md)
- [Procedural memory](procedural.md)
