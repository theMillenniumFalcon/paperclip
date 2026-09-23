# Hosted Paperclip Memory (connect)

Code: `paperclip/tools/paperclip_memory.py`

Not a model tool. Adds the **hosted** MCP memory server to `mcp.json` and signs you in. Local SQLite memory (`paperclip/memory/`) is separate and is **not** uploaded.

Server: `https://paperclip-api.vercel.app/mcp` (`oauth: true`). After a Paperclip restart, MCP tools load as `paperclip_memory_*`.

```
paperclip connect paperclip-memory
```

(or `/connect paperclip-memory` in dashboard chat). Docs for other agents: `https://www.paperclip.one/docs`. Needs `pip install 'paperclip-agent[mcp]'` (`mcp` import).

## `add_server(home)`

Ensures `.paperclip/mcp.json` (the given `home`) lists this server. Returns `(status, spec)`:

| Status | Meaning |
| --- | --- |
| `present` | Some entry already has the current URL |
| `conflict` | That **name** points at some other URL on purpose — left unchanged |
| `added` | Appended `{name, url, oauth: true}` |

## `status(home)`

One line for `paperclip connections`. **Files only** — never opens a browser.

- missing / wrong JSON / no matching URL → not connected
- `auth_env` set → API key (no OAuth)
- no `mcp` extra → tell the user to install it
- no token file → configured, not signed in
- else → `connected ·` plus [CLI identity](mcp-cli.md)

## `connect(home)`

Install extra if needed → `add_server` → conflict message, or skip browser if already signed in (`present` + token; switch with `paperclip mcp login paperclip_memory`). Else `sign_in` (drops token, then OAuth). Remind the user to restart so `paperclip_memory_*` tools load.
