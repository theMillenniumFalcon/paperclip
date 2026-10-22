# Provider errors

Code: `paperclip/loop/errors.py`

Rate limits, rejected keys, timeouts, and other provider HTTP failures are operational. They are logged as one WARNING and returned as a reply. They do not print a traceback, and they do not exit the CLI.

Bugs (`TypeError`, `ValueError`, `KeyError`, and anything else that is not a provider failure) still raise.

## What counts

Matched by exception class name (Anthropic and OpenAI SDKs use the same names) or by `status_code`:

| Kind | Match | Reply starts with |
| --- | --- | --- |
| `rate_limit` | `RateLimitError` or status 429 | `The model provider rate-limited this request` |
| `auth` | `AuthenticationError`, `PermissionDeniedError`, status 401 or 403 | `The model provider rejected the API key` |
| `unreachable` | `APITimeoutError`, `APIConnectionError`, `TimeoutError`, `ConnectionError` | `Couldn't reach the model provider` |
| `api` | other `APIError` / `APIStatusError` names, or any status ≥ 400 | `The model provider returned an error` |

The reply appends that short detail and `This chat is still open.`

`provider_detail` prefers `exc.body["error"]["message"]` (OpenRouter's JSON), then `exc.message`, then `str(exc)`. Whitespace is collapsed and the text is capped at 400 characters. Sentences that mention credits, billing, upgrades, subscriptions, purchases, payments, or unlocks are dropped, so a free-tier limit is reported as the limit name only.

## Logging

`configure_logging` attaches one stderr handler to the `paperclip` logger if it has none:

```text
WARNING paperclip - RateLimitError: Rate limit exceeded: free-models-per-day.
```

The chat reply for that same failure is:

```text
The model provider rate-limited this request: Rate limit exceeded: free-models-per-day. This chat is still open.
```

`log_provider_error` calls that setup, then logs at WARNING **without** `exc_info`. `Paperclip()` configures this on startup so CLI, voice, Telegram, and the dashboard share the format.

## Where it is caught

| Site | Behavior |
| --- | --- |
| Retrieval gate | Provider failures propagate. Parse errors and other exceptions still fail open. |
| `app.respond` | Catches a provider failure from the gate (or anything before the loop). Sets `LoopResult.error`, skips history, `chat_log`, consolidation, and `MEMORY.md`. |
| `run_loop` | Catches a provider failure on `messages.create` / `messages.stream`. Same `LoopResult.error` and an `error` observer event (`error`, `detail`). A stream failure that is **not** a provider error still falls back to a non-streaming `create`. |

The OpenAI adapter does not retry these. It retries only when the provider rejects the name `max_completion_tokens`. See [models](models.md).
