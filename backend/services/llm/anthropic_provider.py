"""Anthropic / Claude provider. Uses the official `anthropic` Python SDK.

Default model: `claude-opus-4-7` (per project policy — override via settings or per-call).
Uses adaptive thinking for high-quality script/validation output.
"""
from __future__ import annotations

from typing import Any

import anthropic
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from backend.services.llm.base import BaseLLMProvider, LLMResponse

log = structlog.get_logger()

DEFAULT_MODEL = "claude-opus-4-7"
DEFAULT_MAX_TOKENS = 16_000


class AnthropicProvider(BaseLLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, default_model: str = DEFAULT_MODEL) -> None:
        if not api_key:
            raise ValueError("AnthropicProvider requires an API key (ANTHROPIC_API_KEY).")
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self.default_model = default_model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((anthropic.APIConnectionError, anthropic.RateLimitError, anthropic.InternalServerError)),
        reraise=True,
    )
    async def complete(
        self,
        system: str,
        user: str,
        *,
        model: str | None = None,
        json_mode: bool = False,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        thinking: bool = True,
        **_: Any,
    ) -> LLMResponse:
        chosen_model = model or self.default_model

        if json_mode:
            user = f"{user}\n\nRespond ONLY with a single valid JSON object. No prose, no markdown fences."

        kwargs: dict[str, Any] = {
            "model": chosen_model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        if thinking:
            kwargs["thinking"] = {"type": "adaptive"}

        log.info("llm.anthropic.call", model=chosen_model, json_mode=json_mode, thinking=thinking)
        msg = await self._client.messages.create(**kwargs)

        text = next((b.text for b in msg.content if b.type == "text"), "")
        usage = {
            "input_tokens": msg.usage.input_tokens,
            "output_tokens": msg.usage.output_tokens,
            "cache_read_input_tokens": getattr(msg.usage, "cache_read_input_tokens", 0),
            "cache_creation_input_tokens": getattr(msg.usage, "cache_creation_input_tokens", 0),
        }
        return LLMResponse(text=text, model=chosen_model, provider=self.name, usage=usage, raw=msg)
