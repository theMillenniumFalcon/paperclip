# Discord gateway

Code: `paperclip/gateway/discord.py`

Talk to Paperclip from **DMs** or (only if you opt in) specific **server channels**. Uses [`GatewayAgentRunner`](runner.md) (`session_id="discord"`, `source="discord"`) and `cli._observer` on the laptop.

**Warning:** The bot uses **your** agent — `.paperclip/state.db`, tools, API key. Anyone it answers can probe your memory; their chat can be **consolidated into your facts**. A bot in a busy server is cost + privacy + memory integrity risk. Default posture is **deny**; server channels are off unless explicitly allowlisted.

## Setup

1. [Discord Developer Portal](https://discord.com/developers/applications) → create bot → enable **Message Content Intent**.
2. `.env`: `DISCORD_BOT_TOKEN=...`, invite bot to server if needed.
3. Extra: `pip install 'paperclip-agent[discord]'`.
4. Run: `make discord` or `python -m paperclip.gateway.discord`.

`describe_posture()` prints who can reach the bot, where it answers, which home dir, and hourly cap.

## Environment

| Variable | Default / empty behavior |
| --- | --- |
| `DISCORD_BOT_TOKEN` | Required to start |
| `DISCORD_ALLOWED_USER` | Comma-separated user ids. **Empty = any user** (subject to channel rules). Set to lock DMs to known people. |
| `DISCORD_ALLOWED_CHANNEL` | Comma-separated channel ids. **Empty = no server channel answered** (DMs only). Must list channels to enable server replies. |
| `DISCORD_REQUIRE_MENTION` | Default `1` — in servers, reply only when @-mentioned. `0` = reply without mention (risky). |
| `DISCORD_MAX_TURNS_PER_HOUR` | Default `30`. Rolling hour; over limit → **silent ignore** (no error reply that invites more messages). |
| `DISCORD_HOME` | If set, separate Paperclip data dir for the bot (community bot ≠ your personal `.paperclip`). |

## Access policy — `should_answer(...)`

Pure function (testable without Discord):

1. If `DISCORD_ALLOWED_USER` is set and author not in list → **no**.
2. **DM** → **yes** (if user check passed).
3. **Server** → **no** unless `channel_id` is in `DISCORD_ALLOWED_CHANNEL`.
4. In an allowed channel → need @-mention unless `DISCORD_REQUIRE_MENTION` is off.

Ignored messages get **no reply** (not a “go away” message).

`TurnBudget` tracks timestamps in the last 3600s; `allow()` enforces the hourly cap.

`_strip_mention` removes `<@id>` / `<@!id>` before the model sees the text.

## Agent factory

`_build_agent()`: `Paperclip()` or `Paperclip(settings)` with `settings.home = DISCORD_HOME` when set.

## Entry points

| Function | Role |
| --- | --- |
| `main()` | Blocking `client.run(token)`; `runner.close()` in `finally` |
| `start_in_background()` | Daemon thread for dashboard; `None` if no token or missing extra |
| `_build_client(runner?)` | `discord.Client` + `on_message` handler |

Handler: skip self/empty; policy + budget; typing indicator; `run_gateway_turn(..., message.reply)`.

## `DiscordHandle`

| Method | Behavior |
| --- | --- |
| `stop()` | Close client on its loop, join thread, `runner.close()` |
| `status()` | `IntegrationStatus` — [Integrations](../integrations.md) |

- Thread dead or client closed → `ERROR`
- `runner.error_status` → `ERROR`
- `client.is_ready()` → `CONNECTED`
- Else → `INSTALLED_BUT_UNCONFIGURED` (“starting”)

## Run

```bash
python -m paperclip.gateway.discord
```
