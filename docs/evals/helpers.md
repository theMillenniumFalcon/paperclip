# Eval helpers

Code: `evals/helpers.py`

## `HAS_KEY`

`True` when `ANTHROPIC_API_KEY` is set. Live dataset cases and the judge suite skip otherwise. This is not “any provider key.”

## Fakes

| Helper | Builds |
| --- | --- |
| `text_block(text)` | `type="text"` |
| `tool_block(name, args, call_id="tu_1")` | `type="tool_use"` |
| `response(blocks, stop_reason="end_turn")` | Object with `stop_reason`, zero `usage`, `content` |

## `ScriptedClient(script)`

`messages.create` pops the next scripted response. No network. No `messages.stream`.

## `make_paperclip(home, client=None, **settings_overrides)`

`Paperclip(settings=Settings(home=home, ...), client=client)`.

- `apple_calendar` defaults to `False` so a developer `.env` cannot sync tests into Calendar.app.
- If `client` is set and `settings.api_key` is empty, `api_key` is set to `"offline"` so a scripted run does not require a real key. `Paperclip` still uses the passed `client` and does not call `get_client`.
