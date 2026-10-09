# Gateway

Code: `paperclip/gateway/`

A **gateway** only moves text (or speech) in and out; the loop, memory, and tools do the work. Same `Paperclip.respond` pipeline as elsewhere, with a different transport.

**Docs are the reference for gateway code.** Each module’s one-line docstring points at its page below. Behavior, setup, env vars, and non-obvious engineering notes live in docs—not in comments in the source.

| Path | Doc | Role |
| --- | --- | --- |
| `cli.py` | [cli.md](cli.md) | Terminal REPL; shared `_observer` for other gateways |
| `telegram.py` | [telegram.md](telegram.md) | Telegram bot (long polling) |
| `voice.py` | [voice.md](voice.md) | Microphone in, TTS out (wake-word or push-to-talk) |

## Run

```bash
python -m paperclip.gateway.cli
python -m paperclip.gateway.telegram
python -m paperclip.gateway.voice
```

Voice: optional `[voice]` extra (`faster-whisper`, `sounddevice`, `numpy`). Telegram: `python-telegram-bot` (project dependency).

## Shared pieces

- **`_observer`** (`cli.py`) — `(kind, event)` callback passed to `respond`. Telegram and voice import it so tool/gate/consolidation lines print on the laptop terminal.
- **`session_id`** — `"terminal"`, `"telegram"`, or `"voice"` so the unified inbox keeps separate threads.
- **`source`** — `"cli"`, `"telegram"`, or `"voice"` on each `respond` call.
