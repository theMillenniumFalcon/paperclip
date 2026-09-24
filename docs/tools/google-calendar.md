# Google Calendar

Code: `paperclip/tools/google_calendar.py`

**Read-only** access to the user’s **primary** Google Calendar. No create/update/delete in this module.

Optional deps: `google-auth`, `google-auth-oauthlib`, `google-api-python-client`. If missing, callers get an install hint (`pip install -e '.[gcal]'` in code).

Scope: `calendar.events.readonly`. Errors return a **sentence**, not an exception, so a calendar failure does not crash a chat turn.

## OAuth client (which app asks Google)

| Source | When |
| --- | --- |
| **Bundled** | `BUNDLED_CLIENT_CONFIG` (Desktop app). Used when `{home}/credentials.json` is absent. `client_id` / `client_secret` must be filled for bundled sign-in to work. |
| **Override** | `{home}/credentials.json` — replaces OAuth **client** config only; same read-only scope. |

Desktop client secrets identify the app; each user still approves in the browser. Token is stored only on disk at `{home}/google-token.json`.

## `connect(home)`

The **only** place that may open a browser (`InstalledAppFlow.run_local_server(port=0)`). Run from CLI/dashboard (`paperclip connect google` / `/connect google`), not mid-turn.

Writes refreshed user credentials to `google-token.json`.

## `_load_credentials` / `is_connected`

`_load_credentials`: load token file → refresh if expired (writes back) → return valid creds or `None`. **Never** opens a browser (chat turns must not block on consent).

`is_connected(home)`: `True` if the token file exists. No network; used to decide whether to mention Google.

## `list_google_events(home, start="", end="", limit=20)`

Fetches events from `calendarId="primary"`.

- `start` / `end`: `YYYY-MM-DD`; empty `start` → today; empty `end` → same day as `start`.
- Window is local midnight through end-of-day (+1 day on `timeMax`), not UTC midnight.
- `singleEvents=True`, `orderBy=startTime`, `limit` clamped 1–100 (default 20).
- Each line: `title | start | attendee emails` (attendees omitted if none).
- Not connected → setup hint; API errors → short message with exception type.

Not wired as a `Tool` in this checkout unless another module registers it.
