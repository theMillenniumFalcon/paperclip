# Ops

Code: `paperclip/ops/`

Local operations around a running Paperclip: the browser dashboard, traces, a morning brief, and the eval release gate.

| Path | Doc | Role |
| --- | --- | --- |
| `dashboard.py` | [dashboard.md](dashboard.md) | Stdlib HTTP server on `127.0.0.1` plus `static/` |
| `static/` | [dashboard.md](dashboard.md) | Current UI (`index.html`, `style.css`, `app.js`). No build step |
| `tracing.py` | [tracing.md](tracing.md) | JSONL traces and optional OpenTelemetry |
| `brief.py` | [brief.md](brief.md) | One briefing turn, saved to the outbox |
| `release_gate.py` | [release-gate.md](release-gate.md) | Pytest gate that writes `eval_report.json` |

A later Next.js UI belongs at the repo root in `web/`, not inside `paperclip/ops/static/`. It should call this server’s `/api/*` routes. `static/` stays the no-build UI until that app exists.

## Pages

- [Dashboard](dashboard.md)
- [Tracing](tracing.md)
- [Brief](brief.md)
- [Release gate](release-gate.md)
