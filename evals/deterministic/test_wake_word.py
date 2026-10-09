"""Wake-word matcher. See docs/evals/deterministic.md."""

import pytest

from paperclip.gateway.voice import matches_wake

SHOULD_WAKE = [
    ("paperclip paperclip", "paperclip paperclip"),
    ("Paperclip, paperclip!", "paperclip paperclip"),
    ("paperclippaperclip", "paperclip paperclip"),
    ("so anyway paperclip paperclip schedule it", "paperclip paperclip"),
    ("paperclib paperclip", "paperclip paperclip"),
    ("Hey Paperclip", "hey paperclip"),
    ("hey computer, what's up", "hey computer"),
]

SHOULD_NOT_WAKE = [
    ("what a nice day", "paperclip paperclip"),
    ("wake up call at nine", "paperclip paperclip"),
    ("", "paperclip paperclip"),
    ("paperclip paperclip", ""),
    ("walk to work", "paperclip paperclip"),
    ("わくわく", "paperclip paperclip,わくわく"),
]


@pytest.mark.parametrize("heard,wake", SHOULD_WAKE, ids=[h for h, _ in SHOULD_WAKE])
def test_wakes(heard, wake):
    assert matches_wake(heard, wake)


@pytest.mark.parametrize("heard,wake", SHOULD_NOT_WAKE, ids=[h or "empty" for h, _ in SHOULD_NOT_WAKE])
def test_stays_asleep(heard, wake):
    assert not matches_wake(heard, wake)
