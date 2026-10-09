# Release gate

Code: `paperclip/ops/release_gate.py`

Runs pytest under `evals/` and writes the verdict into the home directory the dashboard reads.

```bash
python -m paperclip.ops.release_gate
```

1. `evals/deterministic` must exit 0. On failure: `eval_report.json` gets `deterministic: fail`, `judge: not run`, process exits 1.
2. If `ANTHROPIC_API_KEY` is set, run `evals/judge`. Failure: `deterministic: pass`, `judge: fail`, exit 1.
3. If that key is missing, judge is `skipped` and the process still exits 0 after deterministic passed.
4. Success: both fields `pass` (or judge `skipped`) and the message `GATE OPEN`.

`report()` writes `{home}/eval_report.json` (latest only) and appends the same JSON line to `{home}/eval_runs.jsonl`. Counts of passed/failed are parsed from pytest `-q` output. The repo root is two levels above this file (`parents[2]`).
