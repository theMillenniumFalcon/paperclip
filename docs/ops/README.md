# Ops

Code: `paperclip/ops/`

Local operations around a running Paperclip: the browser dashboard, traces, a morning brief, and the eval release gate.

| Path | Doc | Role |
| --- | --- | --- |
| `api.py` | [api.md](api.md) | Stdlib HTTP API on `127.0.0.1` (no frontend) |
| `tracing.py` | [tracing.md](tracing.md) | JSONL traces and optional OpenTelemetry |
| `brief.py` | [brief.md](brief.md) | One briefing turn, saved to the outbox |
| `release_gate.py` | [release-gate.md](release-gate.md) | Pytest gate that writes `eval_report.json` |

The cockpit UI is a separate Next.js app. It calls this server’s `/api/*` routes. See [api.md](api.md).

## Pages

- [API](api.md)
- [Tracing](tracing.md)
- [Brief](brief.md)
- [Release gate](release-gate.md)
