# Demo seed

Code: `scripts/demo_seed.py`

Reset `{PAPERCLIP_HOME}` (default `.paperclip`) to a small, curated state for a recording. The old home is copied aside first. `state.db` is cleared in place, never deleted, so a running CLI, dashboard, or `make telegram` keeps a valid connection to the same file.

```bash
python scripts/demo_seed.py                 # clean slate, keeps usage.jsonl
python scripts/demo_seed.py --reset-spend   # also wipe the spend ledger
```

`load_settings()` picks the home directory. Rows are written through the same stores the app uses: `SqliteFactStore`, `SqliteEpisodeStore`, and `create_event` from [calendar](../tools/calendar.md). `Memory.export_markdown()` rewrites `MEMORY.md`.

## What is cleared

When the home directory already exists:

1. `shutil.copytree` to `{home}.bak-YYYYMMDD-HHMMSS` (a copy, not a move).
2. Delete `calendar.ics`, and remove `outbox/`, `skills/`, and `traces/`.
3. Delete `eval_runs.jsonl` and `eval_report.json` so the next `make gate` is the first row.
4. With `--reset-spend`, also delete `usage.jsonl`. Otherwise the spend ledger stays.

`SOUL.md` is left in place. Then `DELETE FROM chat_log, calendar_events, facts, episodes`. FTS triggers on `facts` and `episodes` stay in sync. See [Database](../db.md).

## What is seeded

| Kind | Content |
| --- | --- |
| Fact `user` | Software engineer in India; Upsurge Labs, OpenBio, portfolio nishank.vercel.app |
| Fact `projects` | AI apps and tools, including medcare-ai, safewatch-ai, book2playlist, recipes-ai, smolDB |
| Fact `movies` | Letterboxd reviews: short, two or three lines, tone matching the film |
| Fact `learning` | AI/ML, backend, system design, RAG, embeddings, multi-agent systems, Cloudflare |
| Fact `tech` | Windows and macOS; Bun, Next.js, Tailwind, MongoDB, PostgreSQL, Redis, Supabase |
| Episode | `2026-10-22` — exploring AI projects and practical software ideas |
| Event | "Movie night", `2026-10-24T19:00`–`22:00`, attendee user |

Edit `FACTS`, `EPISODE`, and `EVENT` in the script before recording. Apple Calendar sync stays off (`make_tool` is called without `apple_calendar`).

After it finishes, run `python -m paperclip dashboard` (or `make dashboard`).
