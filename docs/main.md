# Commands

Code: `paperclip/__main__.py`

```bash
python -m paperclip
```

| Args | Runs |
| --- | --- |
| (none) | Terminal chat (`paperclip.gateway.cli`) |
| `dashboard` | Browser cockpit (`paperclip.ops.dashboard`) |
| `voice` | Microphone gateway |
| `telegram` | Telegram poller |
| `brief` | Morning brief into the outbox |
| `skill install <url>` | Download a `SKILL.md` into `{PAPERCLIP_HOME}/skills/` |

Anything else prints that usage line and exits 1.

`paperclip/__init__.py` only sets `__version__ = "0.1.0"`.
