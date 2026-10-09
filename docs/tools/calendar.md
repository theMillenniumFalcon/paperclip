# Calendar tools

Code: `paperclip/tools/calendar.py`

Local events in SQLite `calendar_events` plus `{home}/calendar.ics`. Optional sync to macOS Calendar.app.

## `create_event`

`make_tool(conn, home, apple_calendar=False)`.

Required: `title`, `start` (ISO 8601). Missing either → recovery message, no write.

| Step | Behavior |
| --- | --- |
| End | Empty `end` → start + 1 hour |
| Normalize | `start` / `end` truncated to 16 chars (`YYYY-MM-DDTHH:MM`) |
| Idempotence | Same `title` + `start` already in DB → not duplicated |
| Persist | Insert row, commit |
| ICS | Append `VEVENT` to `{home}/calendar.ics` (`PRODID:-//paperclip//EN`) |
| Apple | If `apple_calendar` (`PAPERCLIP_APPLE_CALENDAR=1`): `sync_to_apple_calendar` |

Return text states the local path and whether Apple sync ran, failed, or was skipped. The model should relay that literally.

### `sync_to_apple_calendar`

macOS only (`osascript`, 30s timeout). Builds AppleScript dates from ISO parts (day set to 1 before month/year so the 31st does not overflow short months). Prefers a calendar named **Paperclip** (`APPLE_CALENDAR_NAME`); if that calendar cannot be created (common on iCloud-only accounts), uses the first writable calendar and reports its name. Timeout / failure: event remains in SQLite + ICS.

## `list_events`

`make_list_tool(conn)`.

Optional `start`, `end` (date prefix), `limit` (default 20, max 100). `start` filters `start >= YYYY-MM-DD`; `end` filters `start <= YYYY-MM-DDT23:59`. Ordered by start. Empty result mentions local `state.db`, not Calendar.app.
