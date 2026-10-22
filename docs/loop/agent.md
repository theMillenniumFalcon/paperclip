# Agent loop

Code: `paperclip/loop/agent.py`

One **turn**: call the model with tools until it replies to the user or hits `max_iterations`.

## `LoopResult`

| Field | Meaning |
| --- | --- |
| `reply` | Final assistant text, iteration-limit message, or provider-error sentence |
| `tool_calls` | List of `{tool, args, output}` for each execution this turn |
| `iterations` | How many model rounds ran |
| `error` | Exception class name when the model call failed (`RateLimitError`, …), else `None` |

## `run_loop(...)`

| Arg | Role |
| --- | --- |
| `client` | Anthropic-shaped client from `get_client` |
| `model` | Model id for this turn |
| `system` | System prompt string |
| `messages` | Working memory; **mutated in place** with assistant + tool messages |
| `tools` | `ToolRegistry` (schemas + execute) |
| `max_iterations` | Hard cap (default 10) |
| `max_tokens` | Per LLM call (default 2048) |
| `observer` | Optional `(kind, event)` — `text`, `llm`, `tool` |
| `stream` | If true and client supports `.messages.stream`, emit `text` deltas then assemble final message. A provider failure (rate limit, auth, timeout, API status) is returned as `LoopResult.error` instead of falling back. Any other stream error falls back to non-streaming `create` |

### Flow

1. **Reason** — `messages.stream` or `messages.create` with `tools.schemas()`. A provider failure returns immediately with `error` set. See [errors](errors.md).
2. Append assistant `content` to `messages`.
3. If no `tool_use` blocks → set `reply` from text blocks and return.
4. **Act** — `tools.execute` for each call; notify `tool`; append user message with `tool_result` blocks.
5. Repeat until step 3 or iteration limit → fixed “iteration limit” reply.

`Observer` kinds: `text` (`delta`), `llm` (`iteration`, `stop_reason`, `usage`), `tool` (`tool`, `args`, `output`), `error` (`error`, `detail`) when a provider call fails. Provider failures are one WARNING log line and a reply; they do not raise. See [errors](errors.md).
