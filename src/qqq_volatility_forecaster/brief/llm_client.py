from typing import Protocol

import anthropic

from qqq_volatility_forecaster import config

FALLBACK_BETA = "server-side-fallback-2026-07-01"


class LlmError(RuntimeError):
    pass


class LlmClient(Protocol):
    model_id: str

    def complete(self, system: str, prompt: str) -> str: ...


class UnavailableLlm:
    def __init__(self, reason: str, model_id: str = config.BRIEF_MODEL):
        self.model_id = model_id
        self.reason = reason

    def complete(self, system: str, prompt: str) -> str:
        raise LlmError(self.reason)


def default_llm() -> LlmClient:
    try:
        return AnthropicLlm()
    except anthropic.AnthropicError as error:
        return UnavailableLlm(str(error))


class AnthropicLlm:
    def __init__(
        self, model_id: str = config.BRIEF_MODEL, client: anthropic.Anthropic | None = None
    ):
        self.model_id = model_id
        self._client = client or anthropic.Anthropic()

    def complete(self, system: str, prompt: str) -> str:
        try:
            response = self._client.beta.messages.create(
                model=self.model_id,
                max_tokens=4000,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                output_config={"effort": "low"},
                betas=[FALLBACK_BETA],
                fallbacks="default",
            )
        except (anthropic.AnthropicError, TypeError) as error:
            raise LlmError(type(error).__name__) from error
        if response.stop_reason != "end_turn":
            raise LlmError(f"stop_reason={response.stop_reason}")
        return "".join(block.text for block in response.content if block.type == "text").strip()
