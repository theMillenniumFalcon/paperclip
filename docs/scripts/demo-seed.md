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
| Fact `user` | YouTube channel Sean's AI Stories, X `@ShenSeanChen`, Chinese accounts 肖恩君Sean |
| Fact `raj` | Close friend, tennis, British slang |
| Fact `sergey` | Close friend, swimming, cooking |
| Episode | `2026-07-11` — confirmed the standing Saturday 5 PM swim with Sergey |
| Event | "Swim with Sergey", `2026-07-11T17:00`–`18:00`, attendee Sergey |

Edit `FACTS`, `EPISODE`, and `EVENT` in the script before recording. Apple Calendar sync stays off (`make_tool` is called without `apple_calendar`).

After it finishes, run `python -m paperclip dashboard` (or `make dashboard`).
