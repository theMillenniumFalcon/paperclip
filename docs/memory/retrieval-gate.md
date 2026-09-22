# Retrieval gate

Code: `paperclip/memory/retrieval_gate.py`

A cheap classifier so the agent does not hit SQLite (or inject stale facts) on every turn. Default-on retrieval is slower **and** it biases answers when memories are irrelevant.

## API

```python
should_retrieve(client, small_model, message) -> tuple[bool, str, str]
# (retrieve?, search_query, reason)
```

`client` must speak Anthropic’s Messages shape (`messages.create`, content blocks), same as the rest of Paperclip.

## Behavior

1. Sends `GATE_PROMPT` with the user message.
2. Expects **JSON only**: `{"retrieve": true/false, "query": "...", "reason": "<5 words>"}`.
3. Parses from the first `{` to the last `}` in text blocks.
4. Prompt policy: math, general knowledge, small talk, self-contained requests → `false`. User’s life, people, plans, history → `true`, plus search keywords (not necessarily the raw message).

`max_tokens=600`. Reasoning models spend a thinking block *before* JSON; a tiny budget truncates the actual answer.

## Fail open

If the call throws, or the model returns no `{`, the function **retrieves anyway**, using the original message as the query. A stale memory is preferred to a missed one.

That interacts with provider setup: if `small_model` is an id the current provider does not serve, the gate errors every turn, fails open, and **looks healthy while always retrieving**. `paperclip/loop/models.py` drops leaked Anthropic small-model ids when switching providers for this reason.
