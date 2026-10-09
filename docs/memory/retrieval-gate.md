# Retrieval gate

Code: `paperclip/memory/retrieval_gate.py`

Cheap classifier so the agent does not search SQLite on every turn (latency + irrelevant memories biasing replies).

## API

```python
should_retrieve(client, small_model, message) -> tuple[bool, str, str]
```

`(retrieve?, search_query, reason)`. `client` must support Anthropic `messages.create` (same as `paperclip/loop`).

## Behavior

1. User message embedded in `GATE_PROMPT`.
2. Expect JSON only: `{"retrieve": bool, "query": "...", "reason": "<short>"}`.
3. Parse substring from first `{` to last `}` in text blocks.
4. Policy in prompt: general knowledge / math / small talk → `false`; user-specific life / people / plans → `true` with search keywords.

`max_tokens=100`.

## Fail open

On any error or missing `{`, return `(True, message, reason)` — retrieve using the **original message** as the query.

If `small_model` is wrong for the active provider, the gate may error every turn and **always retrieve** while still looking “healthy.” Use a valid `PAPERCLIP_SMALL_MODEL` for your [provider](../loop/models.md).

Used by `Memory.gated_retrieve` before `facts.search` and `episodes.search`.
