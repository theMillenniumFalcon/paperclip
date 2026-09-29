# Gateway

Code: `paperclip/gateway/`

A **gateway** only moves text in and out; the loop, memory, and tools do the work. Same idea as Telegram or dashboard chat, with a different transport.

| Path | Role |
| --- | --- |
| `cli.py` | Interactive terminal REPL (`python -m paperclip.gateway.cli` or entry point) |
| `runner.py` | Async gateways: one thread-owned `Paperclip` per bot |

## Pages

- [CLI](cli.md)
- [Runner](runner.md)
