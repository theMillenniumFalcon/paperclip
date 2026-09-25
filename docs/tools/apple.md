# Apple tools (macOS)

Code: `paperclip/tools/apple.py`

Talks to **Calendar**, **Mail**, **Reminders**, and **Notes** via `osascript` (AppleScript). macOS only. Opt-in at the app level (e.g. `apple_tools` / `PAPERCLIP_APPLE_TOOLS=1` when wired); first use triggers **Automation** permission prompts in System Settings.

All calls are **timeout-bounded** and return **error text**, not exceptions, so a slow or denied app does not hang a chat turn.

## Tools (`make_tools()`)

| Name | What it does |
| --- | --- |
| `read_apple_calendar` | Events in the next N days (default 7) from named calendars |
| `read_apple_mail` | Recent inbox rows: subject, sender, date, `message://` link |
| `create_reminder` | New Reminders item; optional `due` string |
| `create_note` | New note in the default Notes folder |

Distinct from [Google Calendar](google-calendar.md) (Google API, read-only OAuth).

## Environment

| Variable | Role |
| --- | --- |
| `PAPERCLIP_APPLE_CALENDARS` | **Required** for calendar reads. Comma-separated calendar names (e.g. `Work,Home`). Without it, the tool refuses and prints how to list names with `osascript`. Querying every calendar on a busy Mac can take minutes; only named calendars are queried. |

## Performance rule

**Do not use AppleScript `whose` filters on large collections.** Calendar.app evaluates predicates per event over Apple Events (~25s+ on hundreds of events). This code pulls **raw columns** (`summary of every event`, `start date of every event`) and filters by date in Python (~4× faster). Same idea for Mail: avoid heavy predicates; bounded loops instead.

Reminders/Notes can be inherently slow (tens of seconds); `_SLOW_APP_TIMEOUT` (25s) is separate from the default 30s.

## Internals

**`ensure_running(app)`** — If the app is not running, `open -gj -a App` (hidden, no focus steal). AppleScript `launch` idioms fail with -600 when the app is closed.

**`_osa(script, timeout, app=...)`** — Runs `osascript -e`. Optionally starts the app first. Timeout → actionable message (permissions dialog vs slow sync).

**`probe_apple_tools()`** — For each of Calendar, Mail, Reminders, Notes: `tell application "X" to return version` (with launch). Raises `RuntimeError` listing failures — used to verify Automation without reading user data.

**Caching** — `_cached(key, ttl, producer)`: calendar 600s, mail 300s.

### Calendar read

Per configured calendar: fetch all summaries + start dates, tab-separated lines `calendar\tsummary\tdate string`. Parse dates with `_parse_applescript_date` (locale-style `Month D, YYYY at H:MM:SS AM/PM`). Keep events whose **local date** falls between today and `days_ahead`. Script timeout scales with calendar count: `20 + 12 * len(cals)`.

### Mail read

Fetches up to `limit` messages (default 20) from the inbox in order. The script defines a `cutoff` from `hours` but does not use it in the loop — the API parameter `hours` is currently unused for filtering.

### Writes

`create_reminder` / `create_note` — single `make new` AppleScript; quotes in note body replaced with `'`.

## Registration

`make_tools()` returns four `Tool` objects. Not registered in minimal `app.py` unless `apple_tools` (or equivalent) is enabled in a fuller build.
