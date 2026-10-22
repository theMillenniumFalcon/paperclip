"""Provider failures as one-line warnings. See docs/loop/errors.md."""

from __future__ import annotations

import logging
import re

_TEMPLATES = {
    "rate_limit": "The model provider rate-limited this request",
    "auth": "The model provider rejected the API key",
    "unreachable": "Couldn't reach the model provider",
    "api": "The model provider returned an error",
}


def configure_logging() -> None:
    """Attach one stderr handler to the `paperclip` logger. Safe to call twice."""
    log = logging.getLogger("paperclip")
    if log.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s - %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.WARNING)
    log.propagate = False


def provider_detail(exc: BaseException) -> str:
    """Short provider message, without billing upsell or the SDK metadata blob."""
    text = _body_message(getattr(exc, "body", None))
    if not text:
        message = getattr(exc, "message", None)
        text = message if isinstance(message, str) and message.strip() else str(exc)
    text = _without_upsell(text)
    if len(text) > 400:
        text = text[:397] + "..."
    return text


def provider_error_reply(exc: BaseException) -> str | None:
    """User-facing sentence for an expected provider failure, or None for a bug."""
    kind = _kind(exc)
    if kind is None:
        return None
    detail = provider_detail(exc)
    lead = _TEMPLATES[kind]
    if detail:
        return f"{lead}: {detail} This chat is still open."
    return f"{lead}. This chat is still open."


def log_provider_error(exc: BaseException) -> None:
    """Log one WARNING line. No traceback — these are operational, not bugs."""
    configure_logging()
    logging.getLogger("paperclip").warning("%s: %s", type(exc).__name__, provider_detail(exc))


def _kind(exc: BaseException) -> str | None:
    name = type(exc).__name__
    status = getattr(exc, "status_code", None)
    if name == "RateLimitError" or status == 429:
        return "rate_limit"
    if name in {"AuthenticationError", "PermissionDeniedError"} or status in {401, 403}:
        return "auth"
    if name in {"APITimeoutError", "APIConnectionError"} or isinstance(exc, (TimeoutError, ConnectionError)):
        return "unreachable"
    if name in {
        "APIError",
        "APIStatusError",
        "BadRequestError",
        "NotFoundError",
        "UnprocessableEntityError",
        "InternalServerError",
        "ConflictError",
    } or (isinstance(status, int) and status >= 400):
        return "api"
    return None


_UPSELL = re.compile(
    r"\b(credit|credits|billing|upgrade|subscribe|subscription|purchase|payment|unlock)\b",
    re.IGNORECASE,
)


def _without_upsell(text: str) -> str:
    flat = " ".join(text.split())
    kept = [part for part in re.split(r"(?<=[.!?])\s+", flat) if part and not _UPSELL.search(part)]
    return " ".join(kept).strip()


def _body_message(body: object) -> str:
    if not isinstance(body, dict):
        return ""
    err = body.get("error")
    if isinstance(err, dict) and isinstance(err.get("message"), str):
        return err["message"]
    message = body.get("message")
    return message if isinstance(message, str) else ""
