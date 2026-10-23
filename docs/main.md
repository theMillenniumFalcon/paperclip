# Commands

Code: `paperclip/__main__.py`

```bash
paperclip
```

`python -m paperclip` runs the same entry point. The installed command comes from the `paperclip` script in `pyproject.toml` (`paperclip-agent` on PyPI).

| Args | Runs |
| --- | --- |
| (none) | Terminal chat (`paperclip.gateway.cli`) |
| `api` | Local JSON API (`paperclip.ops.api`) |
| `voice` | Microphone gateway |
| `telegram` | Telegram poller |
| `brief` | Morning brief into the outbox |
| `skill install <url>` | Download a `SKILL.md` into `{PAPERCLIP_HOME}/skills/` |

Anything else prints `Usage: paperclip [api|voice|telegram|brief|skill install <url>]` and exits 1.

`paperclip/__init__.py` only sets `__version__ = "0.1.0"`.
