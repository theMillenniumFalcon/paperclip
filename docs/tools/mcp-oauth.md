# MCP OAuth

Code: `paperclip/tools/mcp_oauth.py`

Standard MCP authorization: discover the auth server from resource metadata, dynamic client registration, open a browser, catch the loopback redirect, exchange the code. The SDK does that. This file supplies **token storage**, **opening the browser**, and **the callback**.

`auth_env` is the other remote-auth path (a long-lived key). This module is the flow where no secret is pasted into config.

## Constants

| Name | Value | Why |
| --- | --- | --- |
| `AUTH_DIR` | `mcp-auth` | One JSON file per server; a corrupt file costs one connection, not all |
| `CALLBACK_PORT` | `41765` | Fixed: redirect URI is registered at DCR time; a random port would re-register every run |
| `CALLBACK_PATH` | `/callback` | |
| `SIGN_IN_TIMEOUT` | `300` s | Human time on a consent screen. The bridge wait must be **longer** than this |

## `FileTokenStorage`

`{home}/mcp-auth/{sanitised-name}.json`. Server name → filename: alnum, `-`, `_`, max 64 chars.

Bearer credential: mode `0600`, never logged. Write-then-rename (tmp → dest) so a crash cannot replace a good file with a half write; chmod the tmp **before** rename so it is never briefly world-readable.

Missing or invalid JSON reads as `{}` (one extra sign-in, not a crash). Stores `tokens` and `client_info` (dynamic registration).

## Browser callback

`build_provider` returns `OAuthClientProvider` (httpx auth): on 401 the SDK discovers, registers, then calls:

1. **redirect_handler** — print the URL, `webbrowser.open_new_tab` (False on SSH/headless; the printed URL is the fallback).
2. **callback_handler** — if port busy, error. Serve one GET on `127.0.0.1:41765/callback`, poll every 0.5s (do not `join`; that would block the bridge loop). HTML “Signed in.” HTTP logs silenced.

`_CallbackHandler.result` is **class-level**: the handler is constructed per request; an instance attribute would vanish. One sign-in at a time; cleared before the server starts.

Timeout → runtime error. `error` query param → server’s `error` / `error_description`. Else `AuthorizationCodeResult` from `code`, `state`, `iss`.

Client metadata: name Paperclip, `authorization_code` + `refresh_token`, `token_endpoint_auth_method=none`.
