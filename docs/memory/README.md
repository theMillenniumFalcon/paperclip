# Local memory

Code: `paperclip/memory/`

This package is **on-disk memory for one assistant**: durable facts, dated events, **skills** (how to act), a cheap model that decides whether to search, and another that periodically distills chat into those stores.

It is **not** hosted [paperclip Memory](https://paperclip.pages.dev) (the MCP product described in `skills/paperclip-memory/SKILL.md`). Those two stores do not sync.

In this checkout the package is **not wired into the loop yet**. Nothing in `main.py` or `paperclip/loop/` imports it. Tables are created by [`paperclip/db.py`](../db.md) in `state.db`.

## Layout

| Path | Role |
| --- | --- |
| `retrieval_gate.py` | Small LLM: should this turn search memory? |
| `consolidation.py` | Small LLM: after N exchanges, write facts + one episode |
| `semantic/store.py` | SQLite facts + shared FTS5 query helper |
| `episodic/store.py` | SQLite dated episodes |
| `episodic/notion_store.py` | Same episode API against a Notion database |
| `procedural/` | Skills: load, match, install, export |

Empty `__init__.py` files only mark packages. There is no facade like `from paperclip.memory import Memory`.

## Two kinds of memory

| Kind | Question | Example | Store |
| --- | --- | --- | --- |
| Semantic | What do I know? | Alex prefers morning meetings | `SqliteFactStore` |
| Episodic | What happened, and when? | 2026-07-10: planned the Acme demo with Alex | `SqliteEpisodeStore` or `NotionEpisodeStore` |
| Procedural | How should I do this job? | Calendar skill: call `create_event` with these defaults | `SkillLoader` (`SKILL.md` files) |

Search is **ranked keywords (SQLite FTS5 / BM25)**, not embeddings. For one user’s facts that is fast, local, and inspectable with `sqlite3`.

## Two small-model jobs

1. **[Retrieval gate](retrieval-gate.md)** — before touching any store: does this message need memory?
2. **[Consolidation](consolidation.md)** — after enough chat: extract facts + one episode.

Do not search every turn (latency + irrelevant memories biasing the answer). Do not summarize every message (noise + cost).

```
User message
    → should_retrieve()           # cheap LLM → retrieve? + search query
    → if yes: facts.search() + episodes.search()
    → inject hits into the prompt
    → persist the turn in chat_log
    → consolidate_if_due()        # only after N exchanges
         facts + one episode, then consolidated = 1
```

## Intended loop wiring (not implemented here)

1. On each user turn, call `should_retrieve` with the provider’s **small** model (see `paperclip/loop/models.py`: `small_model` is documented as gate + consolidation).
2. If retrieve is true, search both stores with the gate’s query and put results in the prompt as relevant memory.
3. Append user + assistant rows to `chat_log`.
4. After the turn, call `consolidate_if_due(..., every_n=...)`.
5. Dashboard / `manage_memory` tool can CRUD facts and episodes (`list` / `update` / `delete` / `search_with_ids`).

`Settings` in this snapshot has no `small_model` or memory paths yet.

## Schema

`facts`, `episodes`, `chat_log`, and FTS tables — see [Database](../db.md). FTS uses the default **unicode61** tokenizer; query sanitization: [semantic store](semantic.md#fts5-query-helper).

## Pages

- [Retrieval gate](retrieval-gate.md)
- [Consolidation](consolidation.md)
- [Semantic store](semantic.md)
- [Episodic store](episodic.md) (SQLite + Notion)
- [Procedural memory](procedural.md) (skills)
