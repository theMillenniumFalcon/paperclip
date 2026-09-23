# MCP client (`MCPBridge`)

Code: `paperclip/tools/mcp_client.py`

## Start

`start()` reads `mcp.json`, connects every server, returns `list[Tool]`.

Tool **name the model sees** is `_model_safe_name(server, tool)`: Anthropic/OpenAI want `^[a-zA-Z0-9_-]{1,64}$`. MCP allows dots (`memory.remember`). Non-matching chars become `_`; if still longer than 64, keep the **tail** (tool name matters more than the prefix). Dispatch still uses the **original** MCP tool name.

Description is prefixed `[MCP:<server>]`. Empty `inputSchema` becomes `{type: object, properties: {}}`. SDK 1.x used `inputSchema`, 2.x `input_schema` — both are read.

## Connect

`_open_streams`: stdio via `StdioServerParameters`, or HTTP via `create_mcp_http_client` + `streamable_http_client`. Headers or an httpx auth flow (OAuth) go on the client; the bridge owns the client lifecycle on the exit stack.

## Deadlines

Default wait is `timeout * 2` (constructor `timeout` default 30s, so 60s). If any server has `oauth: true` and **no token file yet**, wait `SIGN_IN_TIMEOUT + 60` (see [OAuth](mcp-oauth.md)) so the CLI does not give up while the browser is still open.

## First OAuth run

Sign-in can take longer than the connection that triggered it. When the token is written, that attempt has often already failed. `_connect_all` **retries once** if a token exists now and did not before. Other failures print the exception; for URL servers that are not `ValueError` (config refusals already say enough), also print `_auth_hint` — oauth → check `mcp-auth/`; api key → check `auth_env`.

## Call / close

`call(server, tool, args)` → `_acall` on the loop. Missing session or errors become strings. Content blocks: text, or `[non-text content]`. `close()` acloses the stack (10s), stops the loop, joins the thread (5s).
