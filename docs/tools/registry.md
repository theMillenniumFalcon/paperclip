# Tool registry

Code: `paperclip/tools/registry.py`

## `Tool`

| Field | Role |
| --- | --- |
| `name` | Model-visible name |
| `description` | When to call it |
| `input_schema` | JSON Schema for arguments |
| `fn` | Python callable returning a string |

`to_api()` → `{name, description, input_schema}` for Anthropic `tools=`.

## `ToolRegistry`

| Method | Behavior |
| --- | --- |
| `register(tool)` | Store by name (later register replaces same name) |
| `schemas()` | List of `to_api()` dicts |
| `execute(name, args)` | Call `fn(**args)`. Unknown tool → `Error: unknown tool '…'`. Exception → `Error running {name}: {exc}` (loop keeps going) |

`build_registry` may set `mcp_bridge` on the instance for shutdown (`MCPBridge.close`).
