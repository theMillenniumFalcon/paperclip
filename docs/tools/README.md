# Tools

Code: `paperclip/tools/`

What the model can **call**: a name, a JSON schema, and a Python function. Results come back as strings the loop can put in a `tool_result` block.

This is not hosted paperclip Memory and not skills. Skills tell the model *how* to act; tools are the actual functions.

In this checkout nothing in `main.py` or `paperclip/loop/` registers or executes these tools yet.

## Layout

| Path | Role |
| --- | --- |
| `registry.py` | `Tool` dataclass + `ToolRegistry` (register, schemas, execute) |
| `github.py` | Read-only GitHub via the `gh` CLI (`github_read`) |
| `notes.py` | `save_note` — explicit write into semantic facts |
| `search.py` | `search_web` — Tavily or DuckDuckGo HTML |
| `mcp_client.py` | MCP bridge: stdio / HTTP servers → `Tool`s |
| `mcp_oauth.py` | Browser OAuth + on-disk tokens |
| `mcp_cli.py` | `paperclip mcp` list / login / logout |

Empty `__init__.py` only marks the package.

## Pages

- [Registry](registry.md)
- [GitHub](github.md)
- [Notes](notes.md)
- [Search](search.md)
- [MCP](mcp.md) (client, OAuth, CLI)
