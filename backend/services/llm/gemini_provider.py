"""Gemini provider via Google's Generative Language REST API.

Uses raw HTTPS (httpx) against:
    https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent

Auth: `X-goog-api-key` header. JSON mode: `generationConfig.responseMimeType`.
"""
from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from backend.services.llm.base import BaseLLMProvider, LLMResponse

log = structlog.get_logger()

DEFAULT_MODEL = "gemini-2.5-flash"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(BaseLLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, default_model: str = DEFAULT_MODEL) -> None:
        if not api_key:
            raise ValueError("GeminiProvider requires GEMINI_API_KEY.")
        self.api_key = api_key
        self.default_model = default_model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPError,)),
        reraise=True,
    )
    async def complete(
        self,
        system: str,
        user: str,
        *,
        model: str | None = None,
        json_mode: bool = False,
        **_: Any,
    ) -> LLMResponse:
        chosen_model = model or self.default_model
        url = f"{BASE_URL}/{chosen_model}:generateContent"

        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": user}]}],
        }
        if system:
            payload["system_instruction"] = {"parts": [{"text": system}]}
        if json_mode:
            payload["generationConfig"] = {"responseMimeType": "application/json"}

        log.info("llm.gemini.call", model=chosen_model, json_mode=json_mode)
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "X-goog-api-key": self.api_key,
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        text = ""
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))

        usage_md = data.get("usageMetadata", {})
        usage = {
            "input_tokens": usage_md.get("promptTokenCount", 0),
            "output_tokens": usage_md.get("candidatesTokenCount", 0),
            "total_tokens": usage_md.get("totalTokenCount", 0),
        }
        return LLMResponse(text=text, model=chosen_model, provider=self.name, usage=usage, raw=data)
