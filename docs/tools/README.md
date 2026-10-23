# Tools

Code: `paperclip/tools/`

What the model can **call**: a name, a JSON schema, and a Python function that returns a string. `build_registry` assembles them. Docs are the reference for each module.

## `build_registry(conn, settings, memory=None)`

Always registered:

| Tool | Module |
| --- | --- |
| `create_event` | [calendar.md](calendar.md) |
| `list_events` | [calendar.md](calendar.md) |
| `save_note` | [notes.md](notes.md) |
| `send_message` | [messages.md](messages.md) |
| `search_web` | [search.md](search.md) |
| `github_read` | [github.md](github.md) |

When `memory` is passed: `manage_memory`, `update_soul`, `create_skill` — [memory-admin.md](memory-admin.md).

Opt-in:

| Gate | Tools |
| --- | --- |
| `PAPERCLIP_EXPERIMENTAL=1` | stubs in [experimental.md](experimental.md) |
| `settings.apple_tools` (`PAPERCLIP_APPLE_TOOLS=1`) | [apple.md](apple.md) |
| `{PAPERCLIP_HOME}/mcp.json` exists | [mcp-client.md](mcp-client.md); sets `registry.mcp_bridge` |

Missing `mcp` package: print install hint `pip install 'paperclip[mcp]'` and continue.

## Layout

| Path | Doc |
| --- | --- |
| `registry.py` | [registry.md](registry.md) |
| `calendar.py` | [calendar.md](calendar.md) |
| `notes.py` | [notes.md](notes.md) |
| `messages.py` | [messages.md](messages.md) |
| `search.py` | [search.md](search.md) |
| `github.py` | [github.md](github.md) |
| `memory_admin.py` | [memory-admin.md](memory-admin.md) |
| `apple.py` | [apple.md](apple.md) |
| `experimental.py` | [experimental.md](experimental.md) |
| `mcp_client.py` | [mcp-client.md](mcp-client.md) |

## Settings used here

| Env | Role |
| --- | --- |
| `PAPERCLIP_APPLE_TOOLS` | Register AppleScript tools |
| `PAPERCLIP_APPLE_CALENDAR` | Sync `create_event` into Calendar.app |
| `PAPERCLIP_APPLE_CALENDARS` | Limit which calendars `read_apple_calendar` scans |
| `PAPERCLIP_EXPERIMENTAL` | Register stub tools |
| `TAVILY_API_KEY` or `PAPERCLIP_SEARCH_API_KEY` | Prefer Tavily over DuckDuckGo |
| `PAPERCLIP_HOME` | Outbox, `calendar.ics`, `mcp.json`, skills, `SOUL.md` |
| `PAPERCLIP_GITHUB_REPO` | Default `owner/name` when `github_read` is called without `repo` |
