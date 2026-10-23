# Loop

Code: `paperclip/loop/`

Model access and the per-turn agent loop. **Docs are the reference** for these modules (see `docs/gateway/README.md` for the same convention).

| Path | Doc | Role |
| --- | --- | --- |
| `models.py` | [models.md](models.md) | Four providers (`anthropic`, `openai`, `openrouter`, `gemini`), `get_client`, OpenAI adapter |
| `agent.py` | [agent.md](agent.md) | `run_loop` — reason / tool act / observe until reply |
| `errors.py` | [errors.md](errors.md) | Provider failures as one WARNING line and a reply |

## Pages

- [Models](models.md)
- [Agent loop](agent.md)
- [Provider errors](errors.md)
