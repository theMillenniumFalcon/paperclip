# MCP tools

Code: `paperclip/tools/mcp_client.py`, `mcp_oauth.py`, `mcp_cli.py`

Plug [Model Context Protocol](https://modelcontextprotocol.io) servers into Paperclip’s `ToolRegistry`. Each remote tool registers as `<server>_<tool>`.

Paperclip’s loop is **sync**; the MCP SDK is **async**. `MCPBridge` runs one asyncio loop on a daemon thread, holds every session on that loop in one `AsyncExitStack` (anyio requires enter/exit on the same task), and the sync loop calls tools with `run_coroutine_threadsafe`.

A server that fails to connect is skipped with a warning; Paperclip still starts.

In this checkout nothing in `main.py` wires the bridge or `paperclip mcp` yet.

## Config — `mcp.json`

Default path the CLI uses: `.paperclip/mcp.json` (cwd-relative). The bridge takes any path; OAuth files live in that path’s **parent** / `mcp-auth/`.

Transport is the **shape of the entry**, not a `transport` field. Both `url` and `command` on one server is an error. Remote HTTP+SSE is not supported — streamable HTTP only.

**stdio** (local process):

```json
{"servers": [{"name": "fs", "command": "npx",
              "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
              "env": {}}]}
```

**Streamable HTTP**:

```json
{"servers": [{"name": "paperclip_memory", "url": "https://host/mcp",
              "auth_env": "PAPERCLIP_MEMORY_API_KEY"}]}
```

Remote auth — pick **one** (both is refused):

| Field | Meaning |
| --- | --- |
| `"auth_env": "VAR"` | Bearer token from that env var. The JSON never holds the secret (people paste `mcp.json` into bug reports). |
| `"oauth": true` | Browser sign-in; tokens under `mcp-auth/`. |

Missing `auth_env` variable fails before connect (otherwise a 401 looks like “server down”).

## Pages

- [Client / bridge](mcp-client.md)
- [OAuth](mcp-oauth.md)
- [CLI](mcp-cli.md)
