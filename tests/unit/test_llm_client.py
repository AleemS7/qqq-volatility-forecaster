from types import SimpleNamespace

import pytest

from qqq_volatility_forecaster.brief.llm_client import AnthropicLlm, LlmError, UnavailableLlm


class FakeMessages:
    def __init__(self, response):
        self.response = response
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return self.response


def _client(stop_reason="end_turn"):
    response = SimpleNamespace(
        stop_reason=stop_reason,
        content=[
            SimpleNamespace(type="thinking", thinking=""),
            SimpleNamespace(type="text", text=" Summary. "),
        ],
    )
    messages = FakeMessages(response)
    return SimpleNamespace(beta=SimpleNamespace(messages=messages)), messages


def test_returns_text_blocks_only():
    client, messages = _client()
    assert AnthropicLlm(client=client).complete("sys", "prompt") == "Summary."
    assert messages.kwargs["fallbacks"] == "default"
    assert messages.kwargs["system"] == "sys"


@pytest.mark.parametrize("reason", ["refusal", "max_tokens"])
def test_non_final_stop_raises(reason):
    client, _ = _client(reason)
    with pytest.raises(LlmError):
        AnthropicLlm(client=client).complete("sys", "prompt")


def test_unavailable_always_raises():
    with pytest.raises(LlmError):
        UnavailableLlm("no key").complete("sys", "prompt")
