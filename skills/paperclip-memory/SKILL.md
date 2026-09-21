---
name: paperclip-memory
description: Connect paperclip Memory, hosted cross-agent memory in Claude Code, Codex, Grok Bot, Hermes. Export paperclip skills.
---

## What paperclip Memory is

This app's memory is local. It lives in `.paperclip/` on this machine and never
leaves it. paperclip Memory (paperclip.pages.dev) is a separate, hosted memory that several
agents share over MCP: a fact saved in Claude Code can be recalled in Codex,
Grok Bot or this app. The two stores are separate, so never tell the user that
local memory syncs to paperclip Memory.

## Connecting this app

Connecting opens the user's browser, so you cannot do it for them. Tell them to
type `/connect paperclip-memory` in the dashboard chat, or to run
`paperclip connect paperclip-memory` in a terminal. It needs the MCP extra:
`pip install 'paperclip-agent[mcp]'`. After it connects, a restart of paperclip loads the
`paperclip_memory_*` tools.

## Connecting other agents

- **Claude Code, Codex, Hermes:** point them to https://www.paperclip.pages.dev/docs.
- **Grok Bot:** Settings → Plugins → add a custom connector with the URL
  `https://paperclip-api.pages.dev/mcp` and the header `Authorization: Bearer <key>`,
  using a key from paperclip.pages.dev → Account → Keys. Its connector form takes a URL
  and a header, not a browser sign-in, which is why it needs the key.
- **Muse Code or any other MCP client:** add `https://paperclip-api.pages.dev/mcp` as a
  remote (streamable HTTP) server.

Tell the user to paste a key only into the other agent's own settings, never
into this chat.

## Carrying skills

`paperclip skill export --to claude,codex` copies paperclip's skills into Claude Code's
and Codex's skills folders. `--project` writes to `./.claude/skills`, which
Muse Code also reads. Saving skills into paperclip Memory is not available yet.

## What not to claim

Don't quote prices, plans or limits; point to https://www.paperclip.pages.dev/docs.