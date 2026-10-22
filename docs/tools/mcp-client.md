# MCP client

Code: `paperclip/tools/mcp_client.py`

Turns [Model Context Protocol](https://modelcontextprotocol.io) **stdio** servers into `Tool`s. The agent loop is synchronous; MCP is async. `MCPBridge` runs one asyncio loop on a daemon thread and calls it with `run_coroutine_threadsafe`. One `AsyncExitStack` owns every session (enter and exit on that loop).

## Config

`{PAPERCLIP_HOME}/mcp.json`:

```json
{"servers": [{"name": "fs", "command": "npx",
              "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
              "env": {}}]}
```

`build_registry` starts the bridge when this file exists. A server that fails to connect is skipped (warning printed); others still register.

On Windows, `command` must be `npx.cmd`. The stdio launcher does not resolve `PATHEXT`, so `npx` exits immediately and the warning is `Connection closed`.

`list_tools` returns MCP `Tool` models. The JSON schema lives on the Python attribute `input_schema` (wire alias `inputSchema`). Read that attribute; alias access raises `AttributeError` and the server is skipped.

## `MCPBridge`

| Method | Behavior |
| --- | --- |
| `start()` | Connect servers, return tools named `{server}_{tool}` with description `[MCP:{server}] …` |
| `call(server, tool, args)` | `call_tool`; text blocks joined, or `(no output)`. Errors become a string |
| `close()` | `aclose` the stack (10s), stop the loop, join the thread (5s) |

Default call timeout: 30s. `start()` waits up to `timeout * 2` for connect.

Requires the `mcp` package (`pip install 'paperclip[mcp]'`).
