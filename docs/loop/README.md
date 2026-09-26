# Loop

Code: `paperclip/loop/`

The agent **turn** (tools + model calls) lives here. Today only **model access** is in the repo; the full `run_loop` may live elsewhere or arrive later.

| Path | Role |
| --- | --- |
| `models.py` | Providers, `get_client`, OpenAI ↔ Anthropic adapter |

## Pages

- [Models](models.md)
