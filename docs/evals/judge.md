# Judge evals

Code: `evals/judge/`

Scores are 0–1 with a threshold, not pass/fail assertions on tool rows. The whole module skips unless `ANTHROPIC_API_KEY` is set. Needs the `deepeval` package.

## `AnthropicJudge`

`load_settings()` and `get_client()`. Model is the argument or `settings.small_model`.

`generate(prompt, schema=None)` calls `messages.create` (`max_tokens=1024`). If `schema` is set, the prompt asks for JSON only and the reply is parsed from the first `{` to the last `}` with `schema.model_validate_json`. `a_generate` calls `generate`. `get_model_name()` is `AnthropicJudge(<model>)`.

## `test_response_quality.py`

Two DeepEval `GEval` metrics, threshold `0.6`, both using `AnthropicJudge`:

| Test | What it scores |
| --- | --- |
| `test_scheduling_reply_is_helpful` | Real `respond` on “Schedule a coffee with Alex next Tuesday at 9am”. Helpfulness: addresses the request, confirms the action, concise. |
| `test_reply_uses_remembered_preference` | Inserts fact “Alex prefers morning meetings”, then “Book a catch-up with Alex on Friday”. MemoryUse: reply should use that retrieval context. |
