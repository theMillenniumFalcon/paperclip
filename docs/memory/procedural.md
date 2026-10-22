# Procedural memory (skills)

Code: `paperclip/memory/procedural/`

**How to act** via `SKILL.md` files (Anthropic Agent Skills YAML frontmatter). Loaded from repo `skills/` and `{PAPERCLIP_HOME}/skills/`.

## `loader.py`

### `Skill`

`name`, `description`, `body`, `path` from frontmatter + markdown body.

### `_parse` / `_parse_text`

Require `---` YAML with `name` and `description`; otherwise skip file.

### `SkillLoader(dirs)`

- `refresh()` — `rglob("SKILL.md")` under each dir, parse valid skills.
- `match(message, max_skills=2)` — if any `SKILL.md` mtime changed, refresh.
- **Scoring:** tokens length ≥ 3 from message vs `name + description`; keep overlap ≥ 2; sort by overlap; return top `max_skills`. No embeddings.

`Memory.matching_skills` joins matched bodies as `### name` sections.

## `installer.py` — `install(url)`

Intended CLI: `paperclip skill install <url>` (when wired).

1. `_raw_url` — GitHub `blob` → `raw.githubusercontent.com`; gist → `/raw`.
2. Fetch (15s timeout).
3. Write `{home}/skills/_incoming/SKILL.md` as UTF-8, parse, move to `{home}/skills/<name>/SKILL.md` (replacing that name if it is already installed). The loader reads every `SKILL.md` as UTF-8. Stdout is UTF-8 for this command so the success line can include characters outside the Windows console code page.
4. Invalid frontmatter: delete temp, exit with error.

Only the markdown file is installed, not sibling assets.

## Progressive disclosure (design)

1. Scan all skill frontmatter (cheap).
2. Inject **body** only for matches.
3. Files referenced inside a skill are for the model to read on demand (not handled in this package).

Write `description` with words users actually say; see `skills/TEMPLATE.md`.
