# Connect command

Code: `paperclip/connect.py`

OAuth and browser sign-in **must not** run mid-chat (the user has to click Allow). This module is the **user-initiated** entry:

- Terminal: `paperclip connect <name>`
- Dashboard: `/connect <name>` (same `connect()` in-process on the user’s machine)

If an integration is missing a token, tools should tell the user to use one of those — not open a browser themselves.

Status labels for the dashboard (`configured` vs `connected`, etc.) are defined in [Integrations](integrations.md).

## Registry — `CONNECTORS`

| Name | Implementation |
| --- | --- |
| `google` | `paperclip.tools.google_calendar.connect` |
| `paperclip-memory` | `paperclip.tools.paperclip_memory.connect` |

Names are matched case-insensitively after strip.

## API

**`connect(name, home: Path) -> str`**

Import the target module and call its `connect(home)`. Returns a human-readable result (success, install hint, or error). Unknown name → message + `usage()`.

**`usage() -> str`** — Lists available connector names.

**`cli_main(argv) -> int`**

1. Load `Settings`, `ensure_home()`.
2. Call `connect(argv[0], settings.home)` and print the string.
3. Exit `0` on success path; `1` if argv missing or name not in `CONNECTORS`.

See [Google Calendar](tools/google-calendar.md#connecthome) and [Paperclip Memory](tools/paperclip-memory.md#connecthome) for what each connector does after sign-in.
