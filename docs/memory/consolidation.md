# Consolidation

Code: `paperclip/memory/consolidation.py`

Batch-distill unconsolidated `chat_log` rows into facts + one episode. Summarizing every message is noisy; waiting **N exchanges** gives enough context.

## API

```python
consolidate_if_due(conn, client, small_model, every_n, facts, episodes) -> int
```

Returns count of **facts** written. `0` = not due, LLM/parse failure, or nothing extracted.

`facts`: `SqliteFactStore` (or Supabase store with `add`). `episodes`: `SqliteEpisodeStore`.

## Behavior

1. `SELECT` from `chat_log` where `consolidated = 0`, ordered by `id`.
2. **Due:** `len(rows) < every_n * 2` → return `0` (each exchange = user + assistant row).
3. Format log as `role: content` lines; call `small_model` with `SUMMARIZER_PROMPT` (`max_tokens=600`).
4. Parse JSON from first `{` to last `}`:

   ```json
   {
     "facts": [{"subject": "...", "content": "..."}],
     "episode": "one sentence"
   }
   ```

5. `facts.add(..., source="consolidation")` for rows with subject and content.
6. `episodes.add(episode, happened_at=today)` if episode string present.
7. Mark those chat_log ids `consolidated = 1`, commit.

## Fail closed on write

On LLM or JSON error, return `0` **without** marking consolidated. Contrast with the [retrieval gate](retrieval-gate.md) (fail open).

Triggered from `Memory.maybe_consolidate` with `settings.consolidate_every` and `settings.small_model`.
