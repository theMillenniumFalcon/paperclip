# Procedural memory (skills)

Code: `paperclip/memory/procedural/`

**How to act**, not what happened or what is true. A skill is a folder with a `SKILL.md` in [Anthropic Agent Skills](https://docs.anthropic.com) format. Claude Code, Codex, and Muse Code use the same files, which is why export copies folders rather than inventing a Paperclip-only format.

This is still **local**. Hosted paperclip Memory does not store skills yet (`--to memory` is rejected).

In this checkout: `SkillLoader` / `install` / `export` are not wired to a CLI entry point. `bundled_skill_dirs()` is imported from `paperclip.memory` but is not defined there yet. `Settings.home` is used but not on `Settings` in `paperclip/config.py` yet.

## Layout

| Path | Role |
| --- | --- |
| `loader.py` | Parse `SKILL.md`, scan dirs, match a user message |
| `installer.py` | Download a remote `SKILL.md` into `PAPERCLIP_HOME/skills/<name>/` |
| `exporter.py` | Copy loaded skills into `.claude/skills` or `.codex/skills` |

## Progressive disclosure

1. Scan frontmatter of every skill (cheap).
2. Load a skill’s **body** into the prompt only when it matches the message.
3. Files a skill mentions are read only if the model asks (not implemented in this package; the loader only returns matching `Skill` objects).

`description` is the trigger. There is no custom `triggers:` field. Write nouns people actually say, not words like *why* / *what* (see `skills/TEMPLATE.md`).

## Loader — `SkillLoader`

`Skill(name, description, body, path)` comes from YAML frontmatter plus body:

```
---
name: ...
description: ...
---
<body>
```

`_parse_text` requires `name` and `description`; otherwise the file is skipped. Same parser is meant for a `create_skill` tool.

**Scan:** `rglob("SKILL.md")` under each dir (typically repo `skills/` plus `PAPERCLIP_HOME/skills`). Invalid files are ignored.

**Reload:** `match()` compares `(path, mtime)` of every `SKILL.md` to the last scan; if anything changed, it refreshes so a skill written mid-session can apply next turn.

**Match:** lowercase tokens of length ≥ 3 from the message vs `name + description`. Keep skills with **overlap ≥ 2**, sort by overlap descending, return at most `max_skills` (default 2). No embeddings.

## Installer — `install(url)`

Meant as `python -m paperclip skill install <url>`.

1. Rewrite GitHub `blob` URLs to `raw.githubusercontent.com`, Gist pages to `/raw`.
2. Fetch with a 15s timeout.
3. Write to `PAPERCLIP_HOME/skills/_incoming/SKILL.md`, parse, then rename to `skills/<name>/SKILL.md`.
4. Invalid frontmatter deletes the temp file and exits.

Only the markdown file is installed, not sibling assets. The exporter skips any skill whose folder path contains `_incoming`.

## Exporter — `export` / `cli_main`

Meant as `paperclip skill export`.

```
paperclip skill export                         # ~/.claude/skills/<name>/
paperclip skill export --to claude,codex
paperclip skill export --project               # ./.<target>/skills (Muse Code reads ./.claude/skills)
paperclip skill export --force                 # replace copies that differ
```

Sources: `bundled_skill_dirs()` then `home/skills`. Later same `name` wins, so home overrides bundled.

Skips a `SKILL.md` whose parent is a skills **root** (copying that would copy every skill) or `_incoming`.

If the destination exists: identical file bytes → `unchanged`; different and no `--force` → `kept yours` (other-agent edits); `--force` replaces.

A skill that calls Paperclip-only tools (e.g. `create_event`) still copies as instructions; the other agent may not have those tools.
