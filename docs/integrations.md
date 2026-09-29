# Integrations

Code: `paperclip/integrations.py`

Shared types for **user-configurable connections** (Google Calendar, Telegram, Tavily, Notion, MCP, …). This file is declarations only — no network I/O. Registries and probe/read/write helpers are expected to import these types so the dashboard, CLI, and health store share one vocabulary.

Browser OAuth entry points live in [Connect](connect.md); this module describes **status**, not how to sign in.

## `IntegrationState`

Where an integration stands, from empty to proven working.

| Value | Meaning |
| --- | --- |
| `not_configured` | Nothing filled in yet |
| `installed_but_unconfigured` | Known integration, but a **required** setting is missing (token, URL, key) |
| `configured` | All required fields present, **not** health-checked yet |
| `connected` | Probed successfully (API or gateway actually works) |
| `error` | Probe or last check failed |

**Why `configured` exists:** Without it, “missing token” and “complete but never probed” both looked like `installed_but_unconfigured`. The dashboard treated that as “needs setup,” so working Tavily keys, live Telegram bots, or connected Notion DBs could show as broken on a fresh checkout with an empty health cache.

## `IntegrationStatus`

Frozen dataclass returned by status/probe code:

| Field | Type | Role |
| --- | --- | --- |
| `state` | `IntegrationState` | One of the values above |
| `message` | `str` | Human detail (error text, hint, empty) |
| `checked_at` | `str \| None` | When last probed (format up to caller) |

## Related

- [Connect](connect.md) — `paperclip connect <name>` for OAuth integrations
- [Tools](tools/README.md) — individual backends (calendar, MCP, search, …)
