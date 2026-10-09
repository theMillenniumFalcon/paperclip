# Tracing

Code: `paperclip/ops/tracing.py`

One `Tracer` is a loop observer. Pass `tracer.event` anywhere an `(kind, event)` callback is expected.

## JSONL (always)

Appends to `{PAPERCLIP_HOME}/traces/YYYY-MM-DD.jsonl`. Each line is one event plus `ts`.

| Call | Writes |
| --- | --- |
| `turn(user_message)` | `turn_start` with `user_message`. Context manager |
| `event(kind, event)` | `{type: kind, ...}`. `kind == "text"` is ignored (live UI only) |
| `event("llm", ...)` | Also appends `{PAPERCLIP_HOME}/usage.jsonl` with provider, model, `in`, `out` |
| `end_turn(reply, iterations)` | `turn_end` |

`usage.jsonl` is the spend ledger the dashboard summarizes. It is separate from the daily trace file.

## OpenTelemetry (optional)

Set `OTEL_EXPORTER_OTLP_ENDPOINT` (`Settings.otel_endpoint`). Then each `turn()` is a root span `agent_run`, and each `event()` inside it is a child span. Attribute prefix is `paperclip.`. Service name is `paperclip`.

If the endpoint is set but `opentelemetry` is not installed, JSONL still runs and a one-line install hint is printed. `end_turn` flushes the provider (2s) so a killed process still exports the span.

## `compose(*observers)`

Returns one callback that forwards `(kind, event)` to every non-empty observer (for example the CLI printer and this tracer).
