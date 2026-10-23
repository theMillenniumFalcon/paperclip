---
name: your-skill-name
description: One sentence saying what this skill does AND when to use it. The loader keeps a skill when the user message shares at least two words (3+ letters) with this name and description, so use the nouns people actually say, not filler like should or about.
---

## Instructions

Step-by-step guidance for the model. Be concrete: name the tools to call, the defaults to assume, and the tone to take.

Tools that exist: `create_event`, `list_events`, `save_note`, `send_message` (local outbox only), `search_web`, `github_read` (read-only `gh`), `manage_memory`, `update_soul`, `create_skill`.

## Where it lives

Copy this file to `skills/<name>/SKILL.md` in the repo, or to `.paperclip/skills/<name>/SKILL.md` for a skill created on this machine. `name` is a short slug: lowercase letters, digits, hyphens (for example `weekly-review`).

## Edge cases

| Situation | Do |
|---|---|
| Something ambiguous | Ask one clarifying question |
