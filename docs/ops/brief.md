# Brief

Code: `paperclip/ops/brief.py`

One agent turn whose prompt asks for the week: calendar, mail that needs attention, and today’s focus. `source="brief"`.

```bash
python -m paperclip.ops.brief
```

Prints the reply with Rich markup off (brackets in the reply stay literal) and writes `{PAPERCLIP_HOME}/outbox/brief-YYYY-MM-DD.txt` as UTF-8.

If `PAPERCLIP_APPLE_TOOLS` is off, prints a tip to set it so Calendar and Mail tools are available. A cron line can call the same command each morning.
