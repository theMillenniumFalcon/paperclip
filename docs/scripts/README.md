# Scripts

Code: `scripts/`

One-off commands that sit next to the package. They are not `python -m paperclip` subcommands. Each script inserts the repo root on `sys.path`, so they run from a checkout without an editable install.

| Path | Doc | Role |
| --- | --- | --- |
| `demo_seed.py` | [demo-seed.md](demo-seed.md) | Backup `PAPERCLIP_HOME`, then write a small curated demo state |
| `validate_skills.py` | [validate-skills.md](validate-skills.md) | Check repo `skills/*/SKILL.md` frontmatter, names, and length |

## Pages

- [Demo seed](demo-seed.md)
- [Validate skills](validate-skills.md)
