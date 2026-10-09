"""LLM-as-judge reply scores. See docs/evals/judge.md."""

from __future__ import annotations

import pytest

from evals.helpers import HAS_KEY, make_paperclip

pytestmark = pytest.mark.skipif(not HAS_KEY, reason="LLM-as-judge needs ANTHROPIC_API_KEY")


@pytest.fixture(scope="module")
def geval_metrics():
    from deepeval.metrics import GEval
    from deepeval.test_case import LLMTestCaseParams

    from evals.judge.anthropic_judge import AnthropicJudge

    judge = AnthropicJudge()
    helpful = GEval(
        name="Helpfulness",
        criteria=(
            "The assistant reply should directly address the user's request, confirm any "
            "action taken (what/when/who), and be concise and warm."
        ),
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        model=judge,
        threshold=0.6,
    )
    uses_memory = GEval(
        name="MemoryUse",
        criteria=(
            "Given the retrieval context (the user's stored memories), the reply should "
            "correctly incorporate relevant remembered facts instead of ignoring them."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.RETRIEVAL_CONTEXT,
        ],
        model=judge,
        threshold=0.6,
    )
    return helpful, uses_memory


def test_scheduling_reply_is_helpful(tmp_path, geval_metrics):
    from deepeval import assert_test
    from deepeval.test_case import LLMTestCase

    helpful, _ = geval_metrics
    app = make_paperclip(tmp_path / "home")
    user_message = "Schedule a coffee with Alex next Tuesday at 9am"
    result = app.respond(user_message)

    assert_test(LLMTestCase(input=user_message, actual_output=result.reply), [helpful])


def test_reply_uses_remembered_preference(tmp_path, geval_metrics):
    from deepeval import assert_test
    from deepeval.test_case import LLMTestCase

    _, uses_memory = geval_metrics
    app = make_paperclip(tmp_path / "home")
    app.memory.facts.add("alex", "Alex prefers morning meetings")
    user_message = "Book a catch-up with Alex on Friday"
    result = app.respond(user_message)

    assert_test(
        LLMTestCase(
            input=user_message,
            actual_output=result.reply,
            retrieval_context=["Alex prefers morning meetings"],
        ),
        [uses_memory],
    )
