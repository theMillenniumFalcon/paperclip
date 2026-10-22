# Manual testing

How to exercise Paperclip by hand, from one process start up to a full conversation that writes memory, files, and traces.

This covers the Python app: `paperclip/`, `evals/`, `scripts/`, and `skills/`. It does not cover the Next.js apps in `web/` and `dashboard/`. The stdlib HTTP API in `paperclip/ops/dashboard.py` is included, because it is part of the Python process. The cockpit UI that calls it is not.

Run the layers in order. Each layer assumes the one before it passed. Stop at the first failure and fix that before widening the scope. Model wording will vary; judge a turn by the **side effect** (a database row, a file, an observer line), not by the exact sentence in the reply.

You are on Windows for the notes below. Apple Calendar, Mail, Reminders, Notes, and the macOS `say` voice only apply on macOS. Skip those cases here.

## Before you start

Use a throwaway home so this does not mix with a real `.paperclip` directory.

PowerShell, from the repo root:

```powershell
$env:PAPERCLIP_HOME = "D:\paperclip\.paperclip-manual"
Remove-Item -Recurse -Force $env:PAPERCLIP_HOME -ErrorAction SilentlyContinue
```

Copy `.env.example` to `.env` if you have not already, and set the key for your provider. The default provider is Anthropic (`ANTHROPIC_API_KEY`). OpenRouter (`PAPERCLIP_PROVIDER=openrouter` plus `OPENROUTER_API_KEY`) and OpenAI (`PAPERCLIP_PROVIDER=openai` plus `OPENAI_API_KEY`) both talk through the `openai` package. `PAPERCLIP_API_KEY` overrides the provider key when set. Leave Apple, Telegram, experimental, Supabase, and OpenTelemetry unset until those layers.

Install dependencies into the project environment, then run Paperclip only through that environment:

```powershell
uv sync
uv run python -c "import paperclip; print(paperclip.__version__)"
```

Expected: `0.1.0`.

Every later `python` command in this doc is prefixed with `uv run`. A bare `python` on PATH is a different interpreter. It does not have the packages from `pyproject.toml`, so `python -m paperclip` with OpenRouter or OpenAI exits immediately:

```text
ModuleNotFoundError: No module named 'openai'
```

The process itself still prints `Usage: python -m paperclip ...`. That line is the program's help text. Launch it with `uv run python -m paperclip`.

## What one turn does

Every gateway calls `Paperclip.respond`. One turn:

1. Builds a system prompt: `SOUL.md`, the local clock, optional retrieved memory, optional matching skills.
2. Runs the model loop until the model replies or hits `PAPERCLIP_MAX_ITERATIONS` (default 10).
3. Appends the exchange to in-memory history and to `chat_log`.
4. Maybe consolidates unconsolidated chat into facts and one episode (default every 6 exchanges).
5. Rewrites `{home}/MEMORY.md`.
6. Appends a JSONL trace and, for each model call, a line in `{home}/usage.jsonl`.

The CLI prints harness lines while that runs:

| Line | Meaning |
| --- | --- |
| `gate · skip — …` or `gate · retrieve — …` | Retrieval gate decided whether to search memory |
| `tool · name({...}) → …` | A tool ran; the tail is the first 80 characters of its output |
| `memory · consolidated N fact(s)…` | Consolidation wrote facts |

## Layer 0 — The process starts

Scope: the command dispatcher. No model call except the last case.

| Do | Expect |
| --- | --- |
| `uv run python -m paperclip nope` | Prints `Usage: python -m paperclip [dashboard\|voice\|telegram\|brief\|skill install <url>]` and exits 1 |
| `uv run python -m paperclip skill` | Same usage line, exit 1 (`skill` without `install <url>` is not a command) |
| Temporarily rename or empty the key for the active provider, then `uv run python -m paperclip` | Process exits with `No API key for provider '<name>'` |
| Set `PAPERCLIP_PROVIDER=nope` and start again | Exits with `Unknown PAPERCLIP_PROVIDER` and the allowed names `anthropic, openai, openrouter` |
| Restore the key and provider, then `uv run python -m paperclip` | A cyan banner: product name, resolved home path, model id, and `Ctrl-D or /quit to exit` |

On the successful start, confirm the home was created:

```powershell
Get-ChildItem $env:PAPERCLIP_HOME
```

Expected directories: `traces`, `outbox`. After the first turn you will also see `state.db`, `SOUL.md`, and `MEMORY.md`.

Quit with `/quit` or Ctrl-C. Expected last line: `bye — your memory stays in state.db`.

## Layer 1 — One chat turn, no tools

Scope: the CLI gateway, the session clock, the retrieval gate on a message that should not search memory, and the trace files. Stay in one `uv run python -m paperclip` session (`session_id` is `terminal`).

| Say | Expect |
| --- | --- |
| *(empty Enter)* | Nothing happens; the prompt returns |
| `What is 17 times 4?` | A reply of 68. A `gate · skip` line (small talk and arithmetic should not retrieve). No `tool ·` line |
| `What day is it?` | The reply matches today's weekday. The system prompt includes the local clock (`Right now it is …`) |
| The same question again | The model can use the previous turn. It should not call a tool |

Then quit and inspect the files the turn always writes.

`state.db` tables:

```powershell
@'
import sqlite3, os
c = sqlite3.connect(os.environ["PAPERCLIP_HOME"] + "/state.db")
print([r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY 1")])
'@ | uv run python -
```

Expected names include `calendar_events`, `facts`, `facts_fts`, `episodes`, `episodes_fts`, `chat_log`.

Chat log for this session:

```powershell
@'
import sqlite3, os
c = sqlite3.connect(os.environ["PAPERCLIP_HOME"] + "/state.db")
for r in c.execute("SELECT role, source, session_id, substr(content,1,80) FROM chat_log ORDER BY id"):
    print(r)
'@ | uv run python -
```

Expected: pairs of `user` / `assistant`, `source` `cli`, `session_id` `terminal`, `consolidated` still `0`.

Trace and spend:

- `{home}/traces/<today>.jsonl` has `turn_start` and `turn_end` lines, plus `gate` and `llm` events. `text` deltas are not written.
- `{home}/usage.jsonl` has one line per model call (`provider`, `model`, `in`, `out`). A gated turn has at least two calls: the small model for the gate, then the main model.
- `{home}/SOUL.md` exists and tells the model which tools it may call.
- `{home}/MEMORY.md` exists. With no facts yet it is mostly a header.

## Layer 2 — One tool at a time

Scope: each always-on tool, still in the CLI. Start a fresh process so history is loaded from `chat_log` for `terminal`. After each prompt, confirm the `tool ·` line names the tool you expected, then confirm the file or row below. Ask for one action per message. The default persona tells the model to call each tool at most once per request.

### `save_note`

Say: `Remember that my bike lock code is 4821.`

Expect a `save_note` call and a reply that includes the subject. Then:

```powershell
@'
import sqlite3, os
c = sqlite3.connect(os.environ["PAPERCLIP_HOME"] + "/state.db")
c.row_factory = sqlite3.Row
for r in c.execute("SELECT id, subject, content, source FROM facts"):
    print(dict(r))
'@ | uv run python -
```

Expected: one row, `source` `user`, subject lowercased. `MEMORY.md` lists that fact.

### `create_event` and `list_events`

Say: `Schedule a dentist appointment tomorrow at 15:00 titled Dentist.`

Expect `create_event`. Then check:

- A row in `calendar_events` with that title. `end` is one hour after `start` when you did not give an end. Times are stored as `YYYY-MM-DDTHH:MM`.
- `{home}/calendar.ics` contains a `VEVENT` whose `SUMMARY` is the title.
- The tool output says the event was saved to the local calendar and that Apple sync was skipped (Apple is off).

Say the **same** sentence again.

Expect the tool output to contain `already exists` and still **one** row and **one** `SUMMARY` in the ICS file.

Say: `What is on my calendar tomorrow?`

Expect `list_events` and the dentist row in the reply. An empty range should say the events live in local `state.db`.

### `send_message`

Say: `Draft a message to Priya saying I will be ten minutes late.`

Expect `send_message`. A new file appears in `{home}/outbox/` named like `YYYYMMDDTHHMMSS-Priya.txt`, body starting with `To: Priya`. The reply must say nothing was actually sent.

### `search_web`

Say: `Search the web for the latest Python release notes.`

Expect `search_web`. With no `TAVILY_API_KEY` and no `PAPERCLIP_SEARCH_API_KEY`, the backend is DuckDuckGo HTML. The tool output is numbered title, snippet, and URL lines. If DuckDuckGo is blocked, the output should tell you to set `TAVILY_API_KEY` rather than inventing links.

Optional, if you have a Tavily key: set `TAVILY_API_KEY`, restart, and repeat. Snippets should be present and no longer than about 400 characters. A nonsense query can return the “try a more specific query” line.

### `manage_memory`

Say: `Search my memory for the bike lock.`

Expect `manage_memory` with `action` `search` and `kind` `fact`. The reply should include the fact id.

Say: `Update fact <id> so the bike lock code is 9999.`

Expect `action` `update`. Re-read `facts`: the content changed, the id did not.

Say: `Delete that fact.`

Expect `action` `delete`. The row is gone and `MEMORY.md` no longer lists it. Episodes cannot be updated; if you ask to edit an episode, the tool should refuse and offer delete.

### `update_soul`

Say: `Always answer scheduling requests with the local file path of the calendar.`

Expect `update_soul`. Open `{home}/SOUL.md`. Under `## Learned rules` there is one new bullet. Ask again with a different rule and confirm it **appends** and does not rewrite earlier bullets.

### `create_skill`

Say: `Create a skill named weekly-review that tells you to list this week's events and then draft a short summary into the outbox. I agree, write the file.`

The model should only write a skill after you agree. Expect `create_skill`. Check `{home}/skills/weekly-review/SKILL.md` has YAML frontmatter with `name` and `description`.

Then say something that shares two content words (3+ letters) with that name and description, for example: `Run my weekly review of events.`

The reply should follow the skill (list events, then an outbox draft). The loader injects at most two matching skills. A skill whose description shares fewer than two such words should not change the reply.

Refuse path: ask to create `weekly-review` again. The tool returns `already exists`. A name that is not `^[a-z0-9][a-z0-9-]{1,40}$` is refused.

## Layer 3 — Working memory and sessions

Scope: history inside one process, and `chat_log` across processes. Still the CLI.

| Do | Expect |
| --- | --- |
| Create an event, then in the **next** message ask `What did you just schedule?` | The reply names the event. The previous assistant row in history contains `[tools used: create_event...]`, which is how the model avoids repeating the call |
| Quit and start `uv run python -m paperclip` again. Ask `What did we schedule?` | The dentist (or later events) come back. History for `terminal` is reloaded from `chat_log` |
| In one sitting, schedule something, quit with Ctrl-C **during** the model call if you can, restart, and ask what was scheduled | A finished turn is durable. A turn killed before `add_exchange` is not in `chat_log` |

`session_id` values you will meet later, each with its own history: `terminal` (CLI), `telegram`, `voice`, `dashboard`, and `brief` only as a `source` tag on `chat_log` (the brief command does not switch the session id unless you do). CLI always sets `terminal`.

There is no CLI command to call `Session.start_new` or `Session.switch`. Those are on the HTTP API in layer 6. Until then, a second conversation means a second `session_id`, which means a different gateway.

## Layer 4 — Retrieval gate and consolidation

Scope: the cheap model (`PAPERCLIP_SMALL_MODEL`, or the provider default).

### Gate

You need at least one fact. Save one: `Remember that Alex prefers morning meetings.`

| Say | Expect |
| --- | --- |
| `What is 2 + 2?` | `gate · skip`. The reply does not mention Alex |
| `When does Alex like to meet?` | `gate · retrieve`. The reply uses the stored preference. `MEMORY.md` is not required for this; retrieval reads SQLite |

Fail-open check (optional): set `PAPERCLIP_SMALL_MODEL` to a model id your provider will reject, restart, and ask `What is 2 + 2?`. The gate errors and **retrieves anyway** (`retrieve` with the original message as the query). The turn can still answer. Put the small model back before continuing. A wrong small model looks healthy and silently searches every turn.

### Consolidation

Default `PAPERCLIP_CONSOLIDATE_EVERY` is 6, meaning 12 unconsolidated `chat_log` rows (each exchange is two rows). For a manual run, narrow it:

```powershell
$env:PAPERCLIP_CONSOLIDATE_EVERY = "2"
```

Restart the CLI. Have four short exchanges that mention a durable fact the model did not already `save_note`, for example your sister's city. On the exchange that crosses the threshold:

- A line `memory · consolidated N fact(s) from recent chats`.
- New `facts` rows with `source` `consolidation`.
- One new `episodes` row whose `happened_at` is today.
- Those `chat_log` rows now have `consolidated = 1`.
- `MEMORY.md` includes the new fact and episode.

If the small model returns junk JSON, consolidation returns 0 and **does not** mark the rows consolidated. The next due turn tries again. That is fail-closed, unlike the gate.

Set `PAPERCLIP_CONSOLIDATE_EVERY` back to `6` (or unset it) when you are done.

### FTS behavior worth one check each

- Fact search ignores one-letter tokens. A query that becomes empty after tokenization returns no facts.
- Episode search with an empty tokenization falls back to the most recent episodes.
- Updating or deleting a fact updates `facts_fts` (database triggers). Search after an update must return the new wording, not the old.

## Layer 5 — Commands that are not the REPL

Scope: one-shot entry points. Keep the same `PAPERCLIP_HOME`.

### Brief

```powershell
uv run python -m paperclip brief
```

Expect:

- A tip that `PAPERCLIP_APPLE_TOOLS` is off, so Calendar.app and Mail are not read.
- A reply about the week. With Apple off, the week comes from local `calendar_events` and memory if the model calls `list_events`.
- A file `{home}/outbox/brief-<YYYY-MM-DD>.txt` whose text matches the reply.
- A `chat_log` pair with `source` `brief`.

Run it twice in one day. The outbox file is overwritten (same date name). Chat log gains another pair.

### Skill install

`uv run python -m paperclip skill install <url>` fetches one `SKILL.md`. Use a raw GitHub URL or a `github.com/.../blob/...` URL (the installer rewrites `blob` to `raw.githubusercontent.com`).

Expect: `Fetching …`, then `Installed '<name>' → {home}/skills/<name>/SKILL.md`. Only the markdown file is saved. An invalid frontmatter (missing `name` or `description`) deletes the temp file and exits with an error.

Point a URL at a page that is not a skill and confirm it fails without leaving `{home}/skills/_incoming/SKILL.md` behind.

### Validate skills

```powershell
uv run python scripts/validate_skills.py
```

This scans **repo** `skills/`, not `{home}/skills`. Expected: `skill validation OK` and the names (at least `paperclip-memory`). Exit 1 lists problems: missing frontmatter, duplicate `name`, a `description` shorter than 5 words, or a body longer than 80 lines.

### Demo seed

This copies the current home to `{home}.bak-<timestamp>` and replaces the database contents. Do it only against `.paperclip-manual`.

```powershell
uv run python scripts/demo_seed.py
```

Expect a backup directory beside the home, `SOUL.md` left in place, `usage.jsonl` kept, and `eval_report.json` / `eval_runs.jsonl` removed. Seeded rows:

- Facts for `user`, `projects`, `movies`, `learning`, and `tech`.
- An episode on `2026-10-22` about exploring AI projects and practical software ideas.
- A calendar event `Movie night` at `2026-10-24T19:00`.

`uv run python scripts/demo_seed.py --reset-spend` also deletes `usage.jsonl`.

Start the CLI and ask `When is movie night?` The gate should retrieve, and the reply should use the calendar event.

## Layer 6 — HTTP API

Scope: `paperclip/ops/dashboard.py` only. Do not start the Next.js app.

```powershell
uv run python -m paperclip dashboard
```

Expected: `Paperclip API -> http://localhost:7777`. If 7777 is taken, it tries the next ports up to +9 and prints each skip. If `TELEGRAM_BOT_TOKEN` is set, it also starts a background Telegram poller; leave the token unset for this layer.

In a second shell, set the same `PAPERCLIP_HOME`. Replace `7777` if the banner showed another port.

| Request | Expect |
| --- | --- |
| `GET http://127.0.0.1:7777/api/data` | JSON with `stats`, `turns`, `facts`, `episodes`, `chat_log`, `sessions`, `soul`, `skills`, `calendar`, `outbox`, `settings`, `tools`, `usage` |
| `GET /api/nope` | `404` and `{"error": "not found"}` |
| `OPTIONS /api/data` with header `Origin: http://localhost:3000` | `204` and `Access-Control-Allow-Origin: http://localhost:3000` |
| Same `OPTIONS` with `Origin: http://evil.example` | No `Access-Control-Allow-Origin` header |
| `POST /api/chat` body `{"message":"What is 3 + 3?"}` | JSON with `reply`, `gate`, `tools`, `iterations`. `source` on the new `chat_log` rows is `dashboard` |
| `POST /api/chat/stream` with the same shape | SSE lines beginning with `data:`. The stream ends with an event whose kind is `done` |
| `POST /api/session` body `{"action":"new"}` | A new session id; later chat in that process uses it |
| `POST /api/session` body `{"action":"switch","id":"terminal"}` | History reloads from `chat_log` where `session_id` is `terminal` |
| `POST /api/session` body `{"action":"history"}` | The current session's pairs |
| `POST /api/query` body `{"sql":"SELECT id, title FROM calendar_events"}` | Up to 200 rows. A statement that is not `SELECT` or `WITH` is rejected |
| `POST /api/memory` | Update or delete a fact or episode, or rewrite soul / save a skill, and see `state.db` or the file change |
| `GET /api/events` | `events` empty and a cursor equal to today's trace line count. Call again after a chat and pass `?cursor=` from the previous response; only new lines return |
| `GET /api/reveal?path=<a file under home>` | Opens that file in `PAPERCLIP_EDITOR`, else `cursor`, else `code`, else the OS file browser. A path outside the home (and outside repo skills) is refused |

`POST /api/settings` writes keys into the `.env` in the working directory (`PAPERCLIP_PROVIDER`, `PAPERCLIP_MODEL`, `PAPERCLIP_SMALL_MODEL`, `TAVILY_API_KEY`, and the active provider key). Empty key values are not written. The response shows only the last 4 characters of secrets. Skip this call unless you intend to change `.env`. After a settings change the process drops the old agent (`close()`) and builds a new one on the next chat.

`POST /api/voice` accepts raw audio bytes and returns `{"text": ...}` using faster-whisper. Skip it until layer 7's voice dependencies are installed.

Two chats at once are serialized by a lock. Send two overlapping `POST /api/chat` calls and confirm both replies arrive and `chat_log` has four new rows with no interleaved half-turns.

Ctrl-C the server when finished.

## Layer 7 — Telegram and voice

Do these only after layers 0–4 pass. Each gateway is the same `respond` path with a different `source` and `session_id`.

### Telegram

1. Create a bot with BotFather and put the token in `TELEGRAM_BOT_TOKEN`.
2. Set `TELEGRAM_ALLOWED_USER` to your numeric id (from @userinfobot).
3. `uv run python -m paperclip telegram`.

Expect: `Paperclip is listening on Telegram`. Send a plain text message. The laptop prints `you ›` / `paperclip ›` and the same harness lines as the CLI. The phone receives the reply. `chat_log.source` is `telegram` and `session_id` is `telegram`, so this thread does not mix with `terminal`.

| Case | Expect |
| --- | --- |
| Message from a different account while `TELEGRAM_ALLOWED_USER` is set | `This Paperclip serves someone else. Run your own!` |
| Unset `TELEGRAM_ALLOWED_USER` and message from another account | The bot answers. Set the allowlist again afterward |
| Send `/start` or another slash command | Ignored (the handler is text that is not a command) |
| Unset the token and start | Exit with instructions to set `TELEGRAM_BOT_TOKEN` |
| Start a second `uv run python -m paperclip telegram` with the same token | The second poller reports a conflict. Stop one of them |

Dashboard interaction: with the token set, `uv run python -m paperclip dashboard` starts the poller on a daemon thread and prints `Telegram gateway → listening in the background`. A phone message during that run is handled. Do not also run `uv run python -m paperclip telegram`; the second poller hits the one-time conflict hint.

### Voice

Install the extra (`sounddevice`, `numpy`, `faster-whisper`) before this. On Windows there is no `say` command. Leave `PAPERCLIP_TTS` empty only if Kokoro imports; otherwise set `PAPERCLIP_TTS=kokoro` or accept the line `(no TTS engine on this platform — set PAPERCLIP_TTS=kokoro)`. The transcript path still works without audio playback.

Whisper defaults to CPU (`PAPERCLIP_WHISPER_DEVICE=cpu`). Leaving the device on `auto` loads CUDA and then fails with `Library cublas64_12.dll is not found or cannot be loaded` when that DLL is not installed. Set `cuda` only after the CUDA 12 runtime is on the machine.

Push-to-talk (simplest):

```powershell
$env:PAPERCLIP_WAKE_WORD = ""
uv run python -m paperclip voice
```

Expect: `Voice Paperclip ready. Press Enter to talk, Ctrl-C to quit.` Press Enter, speak a short sentence, press Enter again.

| Case | Expect |
| --- | --- |
| A normal sentence | `you ›` the transcript, then `paperclip ›` the reply. `source` `voice`, `session_id` `voice` |
| A clip shorter than about 250 ms | `(too short, try again)` |
| Silence | `(didn't catch that)` |
| Ctrl-C | `bye — your memory stays in state.db` |

Wake word: unset `PAPERCLIP_WAKE_WORD` so the default phrases apply (`paperclip`, `paper clip`, and the doubled forms). Expect `Listening for "…"`. Say "paperclip". Expect `[wake word]`, a spoken `Yes?` (`PAPERCLIP_WAKE_ACK`), then a command window. After the reply, the mic stays open for `PAPERCLIP_FOLLOWUP_SECONDS` (default 8) without another wake phrase. Quiet until that window ends and it returns to listening.

Near misses are appended as `wake_scan` events (`matched: false`). They show up in `/api/data` under `wake_scans`.

`PAPERCLIP_MIC_THRESHOLD` (default `0.005`) is the RMS gate. If the room never triggers, lower it. If the fan triggers wake scans constantly, raise it.

`PAPERCLIP_WHISPER_LANG` forces the command language. Leave it empty to let Whisper detect.

## Layer 8 — Optional integrations

Turn these on one at a time, against the same throwaway home, then turn them off.

### Other model providers

Set `PAPERCLIP_PROVIDER` to `openai` or `openrouter`, set that provider's key (`OPENAI_API_KEY` or `OPENROUTER_API_KEY`), unset `PAPERCLIP_MODEL` and `PAPERCLIP_SMALL_MODEL` so the defaults fill in, and restart.

| Provider | Main model | Small model |
| --- | --- | --- |
| `openai` | `gpt-5.5` | `gpt-4.1-mini` |
| `openrouter` | `nvidia/nemotron-nano-9b-v2:free` | `google/gemma-3-4b-it:free` |

Repeat layer 1 (arithmetic, no tool) and one `save_note` from layer 2. The banner shows the resolved model. `usage.jsonl` records that provider. OpenRouter free models are rate-limited; a failure should surface as an error string, not a hung process (`PAPERCLIP_LLM_TIMEOUT` defaults to 120 seconds).

`PAPERCLIP_BASE_URL` overrides the provider URL. Point it at an invalid host and confirm the turn fails with a network error instead of hanging past the timeout.

`PAPERCLIP_API_KEY`, when set, is the key that is used, even if the provider-specific variable is also set.

### Experimental tools

```powershell
$env:PAPERCLIP_EXPERIMENTAL = "1"
```

Restart. Ask the model to delegate a task, run a shell command, browse a page, or schedule a recurring job. The registered names are `delegate_task`, `run_command`, `browse_web`, and `schedule_task`. Each returns a "coming soon" string and must not run a subprocess, open a browser, or write a schedule. Descriptions are prefixed `coming soon`. Unset the variable and confirm a fresh process no longer offers them (the `/api/data` `tools` list is the easy check).

### MCP

Write `{home}/mcp.json`:

```json
{
  "servers": [
    {
      "name": "fs",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "D:\\paperclip\\.paperclip-manual"],
      "env": {}
    }
  ]
}
```

Restart the CLI. On startup the bridge connects. Tools are named `{server}_{tool}` and their descriptions start with `[MCP:fs]`. Ask the model to list files in the home directory and confirm a tool call whose name starts with `fs_`.

| Case | Expect |
| --- | --- |
| `mcp.json` present but the `mcp` package missing | Install hint `pip install 'paperclip[mcp]'`, process continues, no MCP tools |
| One server command that does not exist, plus a good server | A warning for the bad server; the good server's tools still register |
| Quit the CLI | `close()` shuts the bridge. No leftover `npx` process |

### Supabase facts

Only with a project that already has `rag_chunks` and `match_chunks`. Set `PAPERCLIP_SEMANTIC_STORE=supabase`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, and `OPENAI_API_KEY` (embeddings; default model `text-embedding-3-small`). Episodes stay in SQLite.

Save a fact with wording you will not repeat, then ask for it in different words (`My bicycle padlock combination` versus `bike lock code`). Vector search should still hit. Set `PAPERCLIP_SEMANTIC_STORE` back to `sqlite` afterward. SQLite FTS will miss that paraphrase, which is the difference you are checking.

### OpenTelemetry

Set `OTEL_EXPORTER_OTLP_ENDPOINT` to a collector you control (or to a closed port). Take one CLI turn.

- JSONL tracing still happens either way.
- If `opentelemetry` is not installed, one line tells you so, and the turn still completes.
- If it is installed, the turn is a root span `agent_run` with child spans. Attributes are prefixed `paperclip.`. Service name is `paperclip`.

### Apple (macOS only)

Skip on Windows.

| Env | What to check |
| --- | --- |
| `PAPERCLIP_APPLE_CALENDAR=1` | `create_event` also creates the event in Calendar.app, preferring a calendar named Paperclip. The tool output names the calendar or says sync failed. The SQLite row and the ICS file exist either way |
| `PAPERCLIP_APPLE_TOOLS=1` | `read_apple_calendar`, `read_apple_mail`, `create_reminder`, and `create_note` appear. First use raises an Automation permission dialog. A denied or timed-out call returns text; it does not crash the REPL |
| `PAPERCLIP_APPLE_CALENDARS=Work,Home` | `read_apple_calendar` skips other calendars |

`PAPERCLIP_APPLE_CALENDAR` and `PAPERCLIP_APPLE_TOOLS` are independent. The brief tip disappears once Apple tools are on, and the brief can mention real calendar and mail.

## Layer 9 — Wide scenarios

Scope: several subsystems in one sitting. Use the throwaway home after the demo seed, or after your own facts from earlier layers. One CLI session unless a step says otherwise.

### A day in one conversation

1. `Remember that I have a standing Saturday swim with Sergey at 5pm.`
2. `Schedule Swim with Sergey this Saturday at 17:00 for one hour.`
3. `Draft a message to Sergey confirming Saturday at 5.`
4. `Search the web for a public pool open Saturday afternoon near me.` (The model may answer from knowledge if search fails; the `tool · search_web` line is the check.)
5. `What should I remember about Saturday?`

Pass: one `user` fact, one `calendar_events` row, one ICS event, one outbox file, a search tool call, and a final reply that uses the fact or the event (`gate · retrieve`). `traces/<today>.jsonl` contains a `turn_start` / `turn_end` pair per message. `usage.jsonl` grew by at least one line per model call.

### Memory corrects itself

1. Save a wrong fact (`Remember that Raj plays football`).
2. `Search memory for Raj and update the fact so he plays tennis.`
3. Quit, start again, and ask `What sport does Raj play?`

Pass: one fact, content says tennis, the second process retrieves it. `MEMORY.md` matches the row.

### Skill plus tools

1. Install or create a skill whose description uses the words you will say (layer 2 or layer 5).
2. Say that phrase.
3. Confirm the model followed the skill body (the tools it names actually ran).
4. Say an unrelated arithmetic question and confirm the skill body did not leak into the reply.

### Session isolation

1. In the CLI, save a fact and remember the wording.
2. Start Telegram (layer 7) and ask `What did I just tell you in the terminal?`
3. The Telegram thread's **history** is empty, so it should not quote the terminal transcript from working memory.
4. The **fact** is global. `What is my bike lock code?` on Telegram should still retrieve it if the fact is still stored.

Pass: separate `session_id` values in `chat_log`, shared `facts`.

### Consolidation across gateways

With `PAPERCLIP_CONSOLIDATE_EVERY=2`, alternate a CLI turn and a dashboard `POST /api/chat` until consolidation fires. Consolidation reads every unconsolidated `chat_log` row, not only the active session. Pass: one episode covering both sources, and both sources' rows marked `consolidated = 1`.

### Iteration cap

```powershell
$env:PAPERCLIP_MAX_ITERATIONS = "2"
```

Ask for several dependent tool calls in one message (`save a note, create an event, and draft a message`). If the model keeps calling tools, the reply becomes `(I hit my iteration limit before finishing — try breaking the request into smaller steps.)` and `iterations` stops at 2. Unset the variable afterward (default 10).

### Release gate

This is the wide automated check, run by hand at the end:

```powershell
uv run python -m pytest -q evals/deterministic
uv run python -m paperclip.ops.release_gate
```

Deterministic tests do not need a key. They cover scripted `create_event` (including the duplicate), history recording tool use, a no-tool turn finishing in one iteration, the iteration cap, wake-word matching, TTS text cleanup, and the session clock.

The release gate:

| Situation | `eval_report.json` | Process |
| --- | --- | --- |
| Deterministic tests fail | `deterministic: fail`, `judge: not run` | exit 1, `GATE CLOSED` |
| Deterministic pass, no `ANTHROPIC_API_KEY` | `judge: skipped` | exit 0, `GATE OPEN` |
| Deterministic pass, judge below threshold | `judge: fail` | exit 1, `GATE CLOSED` |
| Both pass | both `pass` | exit 0, `GATE OPEN` |

The report is `{home}/eval_report.json` (latest only). The same JSON is appended to `{home}/eval_runs.jsonl`. Judge tests need the `deepeval` package and `ANTHROPIC_API_KEY` specifically, even if you have been chatting through OpenAI or OpenRouter. They are skipped when that key is absent. `GET /api/data` then shows `eval_report` and `eval_history`.

## Checklist

Copy this and mark each line after the layer passes.

- [x] Bad CLI args exit 1 with the usage line
- [x] Missing key and unknown provider exit with a clear message
- [x] Banner shows the throwaway home and the model; `/quit` leaves `state.db`
- [x] Arithmetic turn skips the gate and calls no tool
- [x] `chat_log`, today's trace, `usage.jsonl`, `SOUL.md`, and `MEMORY.md` exist
- [x] `save_note` writes a `user` fact and `MEMORY.md`
- [x] `create_event` writes SQLite and ICS; a repeat does not duplicate
- [x] `list_events` returns that event
- [x] `send_message` writes an outbox file and does not send it
- [x] `search_web` returns links or a clear backend failure
- [x] `manage_memory` can search, update, and delete a fact
- [x] `update_soul` appends a bullet under `## Learned rules`
- [x] `create_skill` writes a skill that matches a later message and refuses a duplicate name
- [x] A second CLI process reloads `terminal` history
- [x] Personal questions retrieve; arithmetic skips
- [ ] With `PAPERCLIP_CONSOLIDATE_EVERY=2`, facts, one episode, and `consolidated = 1` appear
- [x] `brief` writes `outbox/brief-<date>.txt` with `source=brief`
- [x] `skill install` saves one valid skill and rejects bad frontmatter
- [x] `uv run python scripts/validate_skills.py` prints `skill validation OK`
- [x] `uv run python scripts/demo_seed.py` backs up the home and seeds the profile facts, the 2026-10-22 episode, and movie night
- [x] `GET /api/data` matches the database; unknown routes 404
- [x] CORS allows `http://localhost:3000` and not an unknown origin
- [ ] `POST /api/chat` and `/api/chat/stream` complete; `source` is `dashboard`
- [x] Session `new` / `switch` and read-only `/api/query` behave
- [x] Telegram allowlist, text replies, and a second-poller conflict
- [x] Voice push-to-talk transcribes, replies, and rejects a tiny clip
- [x] A second provider completes a no-tool turn and a `save_note`
- [x] Experimental tools return "coming soon" and do nothing else
- [ ] MCP tools from `mcp.json` are callable; a bad server is skipped
- [ ] One multi-step day (fact, event, outbox, search, retrieve) leaves a consistent `state.db`
- [ ] CLI and Telegram share facts and do not share transcript history
- [ ] `uv run python -m paperclip.ops.release_gate` prints `GATE OPEN` or a `GATE CLOSED` you can explain
