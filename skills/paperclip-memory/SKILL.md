---
name: paperclip-memory
description: Paperclip's local memory — facts, episodes, and skills in ~/.paperclip. No hosted sync and no skill export.
---

## What memory is in this app

Memory is local. It lives under `PAPERCLIP_HOME` (default `~/.paperclip/`) and does not leave this machine.

- Durable facts and dated episodes are in `state.db`.
- A readable copy is regenerated as `MEMORY.md`.
- Standing behaviour rules are `SOUL.md`.
- Reusable procedures are `SKILL.md` files under `~/.paperclip/skills/` (and the repo `skills/` folder).

There is no hosted memory connector in this checkout. `paperclip connect paperclip-memory` is named in `paperclip/connect.py`, but `paperclip.tools.paperclip_memory` is not implemented, so do not tell the user to run it. Do not say local memory syncs to another agent or to a website.

## How the user saves and edits memory

Use the tools, do not invent a connect flow:

- **Remember a fact** — `save_note` (explicit). Chat is also distilled into facts and one episode by consolidation after enough turns.
- **Fix or forget** — `manage_memory`: search for the id, then update a fact or delete a fact or episode.
- **A standing rule** ("always …") — `update_soul`, which appends to `SOUL.md`.
- **A repeatable workflow** — `create_skill` only after the user agrees. It writes `~/.paperclip/skills/<name>/SKILL.md`.

`send_message` only writes a file in `~/.paperclip/outbox/`. It does not send anything.

## What not to claim

- Do not offer `paperclip skill export`, or copying skills into Claude Code, Codex, or Muse Code. That exporter is not in this repo.
- Do not quote a hosted memory product, its URL, API keys, prices, or MCP setup for other agents. This app does not ship that integration.
- MCP here is optional local servers in `~/.paperclip/mcp.json` (`docs/tools/mcp-client.md`), not a shared memory service.
