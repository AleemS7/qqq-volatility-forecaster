from qqq_volatility_forecaster.brief.graph import build_graph
from qqq_volatility_forecaster.brief.llm_client import LlmError

METRICS = {
    "status": "ok",
    "date": "2026-10-15",
    "forecast": 18.57,
    "vxn": 22.89,
    "vix": 16.46,
    "rv_21": 16.62,
    "premium": 4.32,
    "backtest_mae": 4.8187,
    "share_overpriced": 0.8039,
}
GOOD = "On 2026-10-15 the model forecast 18.57 and VXN closed at 22.89."
BAD = "On 2026-10-15 the model forecast 18.57 and VXN closed at 25.00."


class FakeLlm:
    model_id = "fake-model"

    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []

    def complete(self, system: str, prompt: str) -> str:
        self.prompts.append(prompt)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def run(replies, metrics=METRICS):
    llm = FakeLlm(replies)
    return build_graph(llm, lambda: metrics).invoke({}), llm


def test_pass_first_try():
    state, llm = run([GOOD])
    assert state["status"] == "llm_verified"
    assert state["attempts"] == 1
    assert state["draft"] == GOOD
    assert "22.89" in llm.prompts[0]


def test_retry_with_corrections_then_pass():
    state, llm = run([BAD, GOOD])
    assert state["status"] == "llm_verified"
    assert state["attempts"] == 2
    assert "unverified number 25.00" in llm.prompts[1]


def test_two_failures_fall_back_to_template():
    state, _ = run([BAD, BAD])
    assert state["status"] == "fallback"
    assert "18.57" in state["draft"] and "22.89" in state["draft"]


def test_llm_outage_falls_back():
    state, _ = run([LlmError("down"), LlmError("down")])
    assert state["status"] == "fallback"
    assert state["errors"] == ["llm error: down"]


def test_outage_then_recovery():
    state, _ = run([LlmError("down"), GOOD])
    assert state["status"] == "llm_verified"


def test_delayed_data_skips_llm():
    state, llm = run([], {"status": "delayed", "date": "2026-10-15"})
    assert state["status"] == "fallback"
    assert "Data delayed" in state["draft"]
    assert llm.prompts == []


def test_prompt_contains_only_facts():
    _, llm = run([GOOD], {**METRICS, "run_id": "secret-run", "model_commit": "abc123"})
    assert "secret-run" not in llm.prompts[0]
    assert "abc123" not in llm.prompts[0]
