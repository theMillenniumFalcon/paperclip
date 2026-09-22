# Consolidation

Code: `paperclip/memory/consolidation.py`

Batch-distill the chat log into long-term memory. Summarizing every message is wasteful and noisy; waiting for N full exchanges gives the model enough context to extract facts worth keeping.

## API

```python
consolidate_if_due(conn, client, small_model, every_n, facts, episodes) -> int
```

Returns how many facts were written. `0` means not due, nothing worth keeping, or the LLM failed.

`facts` is a `SqliteFactStore`. `episodes` is typed as `SqliteEpisodeStore`; a Notion store with the same methods would work at runtime but is not in the type signature.

## Behavior

1. Load `chat_log` rows with `consolidated = 0`, ordered by `id`.
2. **Due check:** `len(rows) < every_n * 2` → return `0`. Each exchange is assumed to be **two rows** (user + assistant). `every_n=5` waits for 10 unconsolidated messages.
3. Cheap model + `SUMMARIZER_PROMPT` over `role: content` lines → JSON:

   ```json
   {
     "facts": [{"subject": "<who/what>", "content": "<one sentence>"}],
     "episode": "<one sentence>"
   }
   ```

4. Write facts with `source="consolidation"`. Skip entries missing subject or content.
5. Write one episode with `happened_at=date.today()` — **today’s date**, not a date extracted from the conversation.
6. Set those `chat_log` ids to `consolidated = 1` and commit.

Prompt policy: only durable facts worth remembering in a month; skip chit-chat; one episode sentence for the whole batch.

`max_tokens=4096` because the prompt includes the full unconsolidated log. A small budget can leave reasoning models with thinking-only replies (`stop_reason=max_tokens`, no text).

## Fail closed on write

If the LLM errors or returns no `{`, return `0` **without** marking rows consolidated. The backlog stays for next time. Contrast with the [retrieval gate](retrieval-gate.md), which fails open.
