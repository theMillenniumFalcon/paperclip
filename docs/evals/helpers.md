# Eval helpers

Code: `evals/helpers.py`

Shared plumbing for offline and (future) live evals.

## `HAS_KEY`

`True` when the **active** provider (`PAPERCLIP_PROVIDER`) has a key: `PAPERCLIP_API_KEY` or that provider’s `key_env` from `paperclip/loop/models.py`. Use `@pytest.mark.skipif(not HAS_KEY, ...)` for tests that call a real model.

## Anthropic-shaped fakes

| Helper | Builds |
| --- | --- |
| `text_block(text)` | `type="text"` content block |
| `tool_block(name, args, call_id=...)` | `type="tool_use"` block |
| `response(blocks, stop_reason=...)` | Full fake `messages.create` return value |

## `ScriptedClient`

Takes a list of those responses. Each `messages.create` pops the next item — a fixed “model” for loop tests without network.

## `make_paperclip(home, client=None, **settings_overrides)`

Builds `paperclip.app.Paperclip` with an isolated `home` directory.

- Pass `client=ScriptedClient([...])` for offline runs. If there is no real `api_key`, sets `api_key="offline"` so `get_client` is never called.
- `settings_overrides` become `Settings(...)` fields (e.g. `gh_tool=True`).

`load_dotenv()` runs at import, so defaults can leak from the developer’s `.env`. For optional Settings flags that change what a turn does (`apple_calendar`, `google_calendar`, `apple_tools`, `graph_workflows`), `make_paperclip` **defaults them to `False`** when those fields exist on `Settings`, so tests stay deterministic unless they opt in.

Only fields that exist on `Settings` are pinned — unknown names on other branches are skipped.
