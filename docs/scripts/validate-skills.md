# Validate skills

Code: `scripts/validate_skills.py`

Check every `SKILL.md` under the repo `skills/` directory. Home-directory skills in `{PAPERCLIP_HOME}/skills/` are not scanned. Parsing uses `_parse` from [procedural memory](../memory/procedural.md): YAML frontmatter must include `name` and `description`.

```bash
python scripts/validate_skills.py
```

Exit `0` prints `skill validation OK` and the skill names. Exit `1` prints each problem. Nothing in this repo invokes the script; it is the check to run on a skill change.

## Rules

| Check | Failure |
| --- | --- |
| At least one `skills/**/SKILL.md` | `no SKILL.md files found under skills/` |
| `_parse` returns a skill | missing or invalid frontmatter (`name` and `description` required) |
| `name` unique across the tree | duplicate name, with the other path |
| `description` has at least 5 words | too short to match a user message |
| Body at most `MAX_BODY_LINES` (80) | skills are loaded into the prompt |

See `skills/TEMPLATE.md` for the frontmatter the loader scores against.
