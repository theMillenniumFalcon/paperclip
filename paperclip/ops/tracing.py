"""JSONL traces and optional OpenTelemetry spans. See docs/ops/tracing.md."""

from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timezone

from paperclip.config import Settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class Tracer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.path = settings.home / "traces" / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        self._otel_tracer = self._init_otel(settings)
        self._span_ctx = None

    def _init_otel(self, settings: Settings):
        if not settings.otel_endpoint:
            return None
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            provider = TracerProvider(resource=Resource.create({"service.name": "paperclip"}))
            provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_endpoint, insecure=True))
            )
            trace.set_tracer_provider(provider)
            self._otel_provider = provider
            return trace.get_tracer("paperclip")
        except ImportError:
            print("(tracing) OTEL endpoint set but opentelemetry not installed — "
                  "pip install opentelemetry-sdk opentelemetry-exporter-otlp. JSONL tracing still on.")
            return None

    def _write(self, record: dict) -> None:
        record["ts"] = _now()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def _record_usage(self, event: dict) -> None:
        usage = event.get("usage", {})
        record = {"ts": _now(), "provider": self.settings.provider,
                  "model": self.settings.model or "", "kind": "loop",
                  "in": usage.get("in", 0), "out": usage.get("out", 0)}
        with (self.settings.home / "usage.jsonl").open("a") as f:
            f.write(json.dumps(record) + "\n")

    def event(self, kind: str, event: dict) -> None:
        if kind == "text":
            return
        if kind == "llm":
            self._record_usage(event)
        self._write({"type": kind, **event})
        if self._otel_tracer and self._span_ctx is not None:
            with self._otel_tracer.start_as_current_span(
                f"{kind}.{event.get('tool', event.get('decision', ''))}".rstrip("."),
                attributes={
                    "openinference.span.kind": {"llm": "LLM", "tool": "TOOL"}.get(kind, "CHAIN"),
                    **{f"paperclip.{k}": json.dumps(v, default=str) for k, v in event.items()},
                },
            ):
                pass

    @contextmanager
    def turn(self, user_message: str):
        self._write({"type": "turn_start", "user_message": user_message})
        if self._otel_tracer:
            with self._otel_tracer.start_as_current_span(
                "agent_run",
                attributes={"openinference.span.kind": "AGENT", "paperclip.user_message": user_message},
            ) as span:
                self._span_ctx = span
                try:
                    yield self
                finally:
                    self._span_ctx = None
        else:
            yield self

    def end_turn(self, reply: str, iterations: int) -> None:
        self._write({"type": "turn_end", "reply": reply, "iterations": iterations})
        if getattr(self, "_otel_provider", None):
            self._otel_provider.force_flush(timeout_millis=2000)


def compose(*observers):
    active = [o for o in observers if o]

    def fanout(kind: str, event: dict) -> None:
        for obs in active:
            obs(kind, event)

    return fanout
