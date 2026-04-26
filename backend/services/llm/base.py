"""Provider contract. Any LLM provider (Claude, OpenAI, Gemini, local, ...) implements this."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    text: str
    model: str
    provider: str
    usage: dict[str, Any] = field(default_factory=dict)
    raw: Any = None


class BaseLLMProvider(ABC):
    """Unified interface over an LLM backend.

    Providers must implement `complete`. `complete_json` has a default implementation
    that appends JSON-only instructions and parses the result, but providers with a
    native JSON mode (OpenAI response_format, Anthropic structured outputs) may override
    it for stricter guarantees.
    """

    name: str = "base"

    @abstractmethod
    async def complete(
        self,
        system: str,
        user: str,
        *,
        model: str | None = None,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion. `json_mode` is a hint; fidelity varies by provider."""

    async def complete_json(
        self,
        system: str,
        user: str,
        *,
        model: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        resp = await self.complete(system, user, model=model, json_mode=True, **kwargs)
        return _safe_json(resp.text)


def _safe_json(raw: str) -> dict[str, Any]:
    import json

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                pass
        return {"_raw": raw, "_parse_error": True}
