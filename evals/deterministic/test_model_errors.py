"""Provider failures stay in the chat. See docs/evals/deterministic.md."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from evals.helpers import make_paperclip
from paperclip.loop.models import retry_with_max_tokens


class RateLimitError(Exception):
    def __init__(self) -> None:
        super().__init__("Error code: 429 - {huge body}")
        self.status_code = 429
        self.message = "Error code: 429 - {huge body}"
        self.body = {
            "error": {
                "message": (
                    "Rate limit exceeded: free-models-per-day. "
                    "Add 10 credits to unlock 1000 free model requests per day"
                ),
                "code": 429,
            }
        }


class RaisingClient:
    def __init__(self, exc_type: type[BaseException], message: str = "boom") -> None:
        self.calls = 0
        self.messages = SimpleNamespace(create=self._create)
        self._exc_type = exc_type
        self._message = message

    def _create(self, **kwargs):
        self.calls += 1
        if self._exc_type is RateLimitError:
            raise RateLimitError()
        raise self._exc_type(self._message)


def test_rate_limit_returns_a_reply_and_skips_memory(tmp_path, capsys):
    client = RaisingClient(RateLimitError)
    app = make_paperclip(tmp_path / "home", client=client)

    result = app.respond("list the files")

    assert client.calls == 1
    assert result.error == "RateLimitError"
    assert result.reply == (
        "The model provider rate-limited this request: "
        "Rate limit exceeded: free-models-per-day. This chat is still open."
    )
    assert "credit" not in result.reply.lower()
    assert app.conn.execute("SELECT COUNT(*) AS n FROM chat_log").fetchone()["n"] == 0
    assert app.session.history == []
    logged = capsys.readouterr().err
    assert "Traceback" not in logged
    assert "WARNING paperclip - RateLimitError: Rate limit exceeded: free-models-per-day." in logged
    assert "credit" not in logged.lower()
    assert "X-RateLimit" not in logged


def test_unexpected_model_error_still_raises(tmp_path):
    client = RaisingClient(ValueError, "bad script")
    app = make_paperclip(tmp_path / "home", client=client)

    with pytest.raises(ValueError, match="bad script"):
        app.respond("hello")

    assert client.calls == 2


def test_retry_with_max_tokens_is_only_the_parameter_mismatch():
    class BadRequestError(Exception):
        pass

    assert retry_with_max_tokens(BadRequestError("unsupported parameter: max_completion_tokens"))
    assert not retry_with_max_tokens(BadRequestError("model not found"))
    assert not retry_with_max_tokens(RateLimitError())
