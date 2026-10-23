# Paperclip

Paperclip is a local personal assistant. The terminal, a microphone, and Telegram all reach the same agent. What it remembers stays in a folder on that machine (`PAPERCLIP_HOME`, default `.paperclip`). Nothing is copied to a hosted account.

One turn is: decide whether to search memory, inject matching skills, call the model with tools until it replies, then log the exchange and sometimes file what it learned.

## Requirements

- Python 3.13 or newer
- An API key for one model provider. The default is Anthropic (`ANTHROPIC_API_KEY`).

Voice also needs a microphone. The packages for speech (`faster-whisper`, `sounddevice`, `numpy`, `kokoro`) are project dependencies.

## Install

Dependencies come from `pyproject.toml` through [uv](https://docs.astral.sh/uv/). From the project folder:

```bash
uv sync
```

That creates `.venv` and installs this package in editable mode. Copy `.env.example` to `.env`. Put your key on `ANTHROPIC_API_KEY`. That is the only line the default setup needs.

```bash
uv run python -m paperclip
```

Run every Python command with `uv run`. A bare `python` on PATH is a different interpreter and does not have the packages from `pyproject.toml`. The process help text still says `python -m paperclip`; launch it with `uv run`.

The banner shows where memory lives and which model is answering. Empty lines are ignored. Leave with `/quit`, `/exit`, or Ctrl-D. Closing the terminal does not delete memory.

## Commands

| Command | What it does |
| --- | --- |
| `uv run python -m paperclip` | Terminal chat |
| `uv run python -m paperclip voice` | Microphone in, speech out |
| `uv run python -m paperclip telegram` | Telegram long-polling (laptop stays the host) |
| `uv run python -m paperclip dashboard` | Local JSON API for the cockpit (`127.0.0.1`, default port `7777`) |
| `uv run python -m paperclip brief` | One morning-brief turn, saved under the outbox |
| `uv run python -m paperclip skill install <url>` | Download a `SKILL.md` into `{PAPERCLIP_HOME}/skills/` |

On Unix, the `Makefile` wraps the same entry points (`make run`, `make voice`, `make telegram`, `make brief`, `make dashboard`, `make eval`, `make eval-judge`, `make gate`). It uses `.venv/bin/python` when `uv sync` has created that interpreter.

## Model providers

Paperclip speaks one dialect (Anthropic Messages). Other providers go through an OpenAI-compatible adapter. Set `PAPERCLIP_PROVIDER` and the matching key. `PAPERCLIP_API_KEY` overrides the provider key when set. Empty `PAPERCLIP_MODEL` and `PAPERCLIP_SMALL_MODEL` fall back to the defaults below.

| `PAPERCLIP_PROVIDER` | Key | Default model | Small model (gate and consolidation) |
| --- | --- | --- | --- |
| `anthropic` (default) | `ANTHROPIC_API_KEY` | `claude-sonnet-5` | `claude-haiku-4-5-20251001` |
| `openai` | `OPENAI_API_KEY` | `gpt-5.5` | `gpt-4.1-mini` |
| `openrouter` | `OPENROUTER_API_KEY` | `nvidia/nemotron-nano-9b-v2:free` | `google/gemma-3-4b-it:free` |
| `gemini` | `GEMINI_API_KEY` | `gemini-3.8-flash` | `gemini-3.5-flash-lite` |

`PAPERCLIP_BASE_URL` overrides the provider URL. `PAPERCLIP_LLM_TIMEOUT` defaults to 120 seconds. `PAPERCLIP_MAX_TOKENS` defaults to 2048. `PAPERCLIP_MAX_ITERATIONS` defaults to 10 (tool rounds per turn).

Judge evals and the release gate look at `ANTHROPIC_API_KEY` only.

## How a turn works

```
user message
  → retrieval gate (small model: search memory this turn?)
  → matching skills (SKILL.md)
  → agent loop: reason → tool calls → observe, until a reply or the iteration cap
  → chat log + in-memory history
  → consolidation every N exchanges (facts + a dated episode)
  → rewrite MEMORY.md
```

A failed model call is not stored as the assistant’s answer. The reply comes back, and the prompt returns.

The persona is `{PAPERCLIP_HOME}/SOUL.md`. If the file is missing, a default is written. Editing it changes the next turn. The system prompt also includes the local clock so relative times (“tomorrow at 3”) can be resolved.

## Memory

Three stores, all local:

| Kind | Question | Where |
| --- | --- | --- |
| Semantic | What do I know? | `facts` in `state.db` (FTS5). Optional Supabase vectors. |
| Episodic | What happened, when? | `episodes` in `state.db` |
| Procedural | How should I act? | `SKILL.md` under repo `skills/` and `{home}/skills/` |

Default search is SQLite FTS5 (BM25). No embeddings unless `PAPERCLIP_SEMANTIC_STORE=supabase`, which also needs `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, and `OPENAI_API_KEY`.

A small model decides whether this turn needs a search (`PAPERCLIP_RETRIEVAL_TOP_K`, default 4). After `PAPERCLIP_CONSOLIDATE_EVERY` exchanges (default 6), another small-model pass files facts and an episode, then rewrites `{home}/MEMORY.md`. You can also ask it to remember something on purpose (`save_note` / `manage_memory`).

`MEMORY.md` is a readable export of SQL. The database is the source of truth: `{PAPERCLIP_HOME}/state.db`.

```bash
sqlite3 .paperclip/state.db ".tables"
```

## Tools

You do not pick a tool by name. Ask in the conversation, and the model calls the one that fits.

| Tool | What it does |
| --- | --- |
| `create_event`, `list_events` | Local calendar rows in `state.db` |
| `save_note` | A fact you asked it to keep |
| `send_message` | A text file in `{home}/outbox`. It does not send email or chat. |
| `search_web` | Tavily when `TAVILY_API_KEY` (or `PAPERCLIP_SEARCH_API_KEY`) is set; otherwise DuckDuckGo |
| `github_read` | Read-only GitHub via the `gh` CLI (issues, pull requests, files). It will not merge, comment, close, or push. |
| `manage_memory`, `update_soul`, `create_skill` | Edit facts, `SOUL.md`, and skills |

Opt-in:

- `PAPERCLIP_GITHUB_REPO=owner/name` is the default repo when `github_read` is called without one. Public repos need no extra auth. Private repos need `gh auth login`.
- `PAPERCLIP_APPLE_CALENDAR=1` also tries to put `create_event` on Calendar.app (macOS).
- `PAPERCLIP_APPLE_TOOLS=1` registers AppleScript tools (Calendar and Mail). Useful for the morning brief.
- `PAPERCLIP_EXPERIMENTAL=1` registers stub tools.
- `{PAPERCLIP_HOME}/mcp.json` starts MCP servers and exposes their tools. If the `mcp` package is missing, Paperclip prints an install hint and continues.

Morning brief:

```bash
uv run python -m paperclip brief
```

The file is `{PAPERCLIP_HOME}/outbox/brief-YYYY-MM-DD.txt`.

## Voice

```bash
uv run python -m paperclip voice
```

Speech is transcribed on the machine (faster-whisper). By default it waits for a wake phrase (`paperclip`, `paper clip`, `paperclip paperclip`, and a few variants), answers `Yes?` (`PAPERCLIP_WAKE_ACK`), then listens. After a reply it stays open for `PAPERCLIP_FOLLOWUP_SECONDS` (default 8) so you can continue without the phrase.

Set `PAPERCLIP_WAKE_WORD` empty for push-to-talk: Enter starts recording, Enter stops it. Clips shorter than a quarter of a second are ignored.

`PAPERCLIP_WHISPER_MODEL` defaults to `base`. `PAPERCLIP_WHISPER_DEVICE=cpu` avoids a missing CUDA runtime. `PAPERCLIP_TTS` and `PAPERCLIP_VOICE` pick how replies are spoken. On macOS, speech uses `say` unless `PAPERCLIP_TTS` is set.

The conversation is stored the same way as terminal chat (`session_id` `voice`).

## Telegram

The assistant still runs on your computer. The process calls Telegram, so you do not need a public address.

1. In Telegram, open @BotFather and send `/newbot`. Copy the token.
2. Set `TELEGRAM_BOT_TOKEN` in `.env`.
3. Set `TELEGRAM_ALLOWED_USER` to your numeric Telegram id (from @userinfobot). If this is empty, anyone who finds the bot can talk to your assistant.

```bash
uv run python -m paperclip telegram
```

Only plain messages are answered. Bot commands are ignored. If the allowlist is set, other people get a short refusal. The laptop prints the message and the reply; you read the reply in Telegram.

If the dashboard is running and `TELEGRAM_BOT_TOKEN` is set, the poller also starts in the background.

## Dashboard

The API and the UI are separate.

```bash
uv run python -m paperclip dashboard
```

That binds a stdlib HTTP server to `127.0.0.1`. Port is `PAPERCLIP_DASHBOARD_PORT`, else `PORT`, else `7777`. If the port is busy, the next ports up to +9 are tried. Startup prints `Paperclip API -> http://localhost:<port>`.

The cockpit (turns, memory, tools, database, evals, spend, settings, chat) is the Next.js app in `dashboard/`:

```bash
cd dashboard
bun run dev
```

It calls `NEXT_PUBLIC_PAPERCLIP_API` (default `http://127.0.0.1:7777`). The browser origin must be in `PAPERCLIP_DASHBOARD_ORIGINS` (default includes `localhost:3000` and `:3001`). `/api/settings` can write API keys, and `/api/reveal` opens files on the host, so CORS is an allowlist.

Chat streaming is `POST /api/chat/stream` (SSE). Call it directly; a Next.js rewrite can buffer the stream.

Traces always append to `{home}/traces/YYYY-MM-DD.jsonl`. Token use is appended to `{home}/usage.jsonl`. Set `OTEL_EXPORTER_OTLP_ENDPOINT` to also export OpenTelemetry spans (the `opentelemetry` packages are optional).

`web/` is the user-facing docs site, separate from the cockpit.

## Home directory

`ensure_home()` creates `home`, `home/traces`, and `home/outbox`. A running install typically looks like this:

```
.paperclip/
  state.db          # facts, episodes, chat_log, calendar
  MEMORY.md         # export of memory
  SOUL.md           # persona
  skills/           # skills installed on this machine
  mcp.json          # optional MCP servers
  outbox/           # send_message drafts and briefs
  traces/           # daily JSONL
  usage.jsonl       # token ledger
  eval_report.json  # latest release-gate verdict
  eval_runs.jsonl   # gate history
```

`PAPERCLIP_HOME` changes the path. The folder is gitignored.

## Skills

A skill is a `SKILL.md` with YAML frontmatter (`name`, `description`) and instructions. The loader keeps a skill when the user message shares at least two words (3+ letters) with the name and description. Copy `skills/TEMPLATE.md` into `skills/<name>/SKILL.md` (repo) or `{home}/skills/<name>/SKILL.md` (this machine).

```bash
uv run python -m paperclip skill install <url>
uv run python scripts/validate_skills.py
```

## Tests

Deterministic tests use a scripted model and do not need an API key. Judge tests score real replies with DeepEval and run only when `ANTHROPIC_API_KEY` is set.

```bash
uv run python -m pytest -q evals/deterministic
uv run python -m pytest -q evals/judge
uv run python -m paperclip.ops.release_gate
```

The release gate requires deterministic tests to pass. If the Anthropic key is missing, the judge is skipped and the process still exits 0. A passing run prints `GATE OPEN` and writes `{home}/eval_report.json`.

`uv run python scripts/demo_seed.py` backs up `PAPERCLIP_HOME` and writes a small curated demo state.

## Layout

```
paperclip/          # the agent
  app.py            # one running agent; gateways call respond()
  config.py         # Settings from the environment
  db.py             # state.db schema
  __main__.py       # CLI entry
  gateway/          # cli, voice, telegram
  loop/             # providers and the tool loop
  memory/           # facts, episodes, skills, gate, consolidation
  runtime/          # SOUL.md and in-memory history
  tools/            # functions the model can call
  ops/              # dashboard API, traces, brief, release gate
evals/              # deterministic tests and LLM judge
dashboard/          # Next.js cockpit
web/                # user docs site
docs/               # engineering reference (canonical for behavior)
scripts/            # demo seed and skill check
skills/             # repo skills
```

## Environment

`.env.example` lists every variable. The ones you usually touch:

| Variable | Default | Role |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | empty | Required for the default provider |
| `PAPERCLIP_PROVIDER` | `anthropic` | `anthropic`, `openai`, `openrouter`, `gemini` |
| `PAPERCLIP_HOME` | `.paperclip` | Memory, traces, outbox, skills |
| `PAPERCLIP_MODEL` | provider default | Main loop model |
| `PAPERCLIP_SMALL_MODEL` | provider default | Retrieval gate and consolidation |
| `TAVILY_API_KEY` | empty | Web search. Unset uses DuckDuckGo |
| `TELEGRAM_BOT_TOKEN` | empty | Telegram gateway |
| `TELEGRAM_ALLOWED_USER` | empty | Numeric user id. Unset means anyone |
| `PAPERCLIP_GITHUB_REPO` | empty | Default `owner/name` for `github_read` |
| `PAPERCLIP_DASHBOARD_PORT` | `7777` | Dashboard API port |
