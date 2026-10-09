# Evals

Code: `evals/`

Pytest suites. Deterministic tests use a scripted model and do not need an API key. Live and judge tests run only when `ANTHROPIC_API_KEY` is set.

`conftest.py` puts the repo root on `sys.path` so `import paperclip` and `import evals` work from `pytest evals`.

## Run

```bash
pytest evals/deterministic -q
pytest evals/judge -q
```

The release gate runs these two folders. See [release gate](../ops/release-gate.md).

## Layout

| Path | Doc | Role |
| --- | --- | --- |
| `helpers.py` | [helpers.md](helpers.md) | `ScriptedClient`, `make_paperclip`, `HAS_KEY` |
| `dataset.jsonl` | [deterministic.md](deterministic.md) | Live tool-trigger cases |
| `deterministic/` | [deterministic.md](deterministic.md) | Offline assertions plus the dataset |
| `judge/` | [judge.md](judge.md) | DeepEval scores on real replies |

## Pages

- [Helpers](helpers.md)
- [Deterministic](deterministic.md)
- [Judge](judge.md)
