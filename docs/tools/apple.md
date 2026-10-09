# Apple tools

Code: `paperclip/tools/apple.py`

macOS only (`osascript`). Registered when `PAPERCLIP_APPLE_TOOLS=1`. First use can show Automation permission dialogs. Failures return text; they do not raise.

Separate from `create_event`’s Apple sync (`PAPERCLIP_APPLE_CALENDAR`).

## Helpers

- `_osa(script, timeout=30)` — run AppleScript; non-darwin, timeout, and nonzero exit become `(False, message)`.
- `_cached(key, ttl, producer)` — in-process cache.

## Tools

| Name | Behavior |
| --- | --- |
| `read_apple_calendar` | Events from now through `days_ahead` (default 7). Cached 600s. Optional `PAPERCLIP_APPLE_CALENDARS=Work,Home` skips other calendars (full enumeration is slow). Timeout 45s. |
| `read_apple_mail` | Inbox since `hours` (default 48), up to 20 messages: subject, sender, date, `message://` link. Cached 300s. |
| `create_reminder` | New Reminders item; optional `due` AppleScript date string. |
| `create_note` | New note in the Notes folder named `Notes`. Quotes in text become apostrophes. |
