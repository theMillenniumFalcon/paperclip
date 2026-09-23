# MCP CLI

Code: `paperclip/tools/mcp_cli.py`

```
paperclip mcp                 list servers and who each one thinks you are
paperclip mcp login <name>    drop the token, then connect (browser sign-in)
paperclip mcp logout <name>   delete the token file
```

Home is **`.paperclip`** in the current working directory (not `Settings.home` in this snapshot).

Two agents on the same memory server, signed in as **two people**, look like a broken server. This command’s job is to **print the account** (email/sub from the stored JWT), then login/logout.

## List

Reads `mcp.json` `servers`. Per entry:

- HTTP + `oauth` → `oauth · <identity>`
- HTTP + `auth_env` → `api key · $VAR`
- HTTP, no auth → `no credential`
- `command` → local process, no credential

Invalid JSON exits 1. Empty config points at [mcp.md](mcp.md).

## Identity

JWT **payload only**, signature not verified — this is describing our own file back to the owner; the server verifies on every call.

- no file → `not signed in`
- unreadable JSON → `unreadable — will sign in again`
- `email` or `sub`, plus expiry: expired → `token expired, refreshes on next use`; else `Nh left` or `Nm left` (not `0h left` for under an hour)

Token path: `FileTokenStorage(home, name)._path`.

## Login (`sign_in`)

Deletes the token **first**. Otherwise a still-valid token never prompts, so “log in as someone else” would keep the old account.

Then `MCPBridge(...).start()` / `close()`. Success is **a token file exists**, not “session is up”. The sign-in can succeed, write the token, and reconnect on a failed stack still error — the CLI would then say it failed after succeeding.

`TimeoutError` → check `paperclip mcp`; the callback may have written the token after the waiter gave up. Other exceptions after start are swallowed; then check whether the file exists. `paperclip connect paperclip-memory` is meant to show `sign_in`’s message in dashboard chat (a `print` would hit the server log).
