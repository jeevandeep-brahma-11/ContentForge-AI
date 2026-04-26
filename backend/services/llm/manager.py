"""LLMManager: registry of providers, resolves which one to use per call.

Active provider is chosen by `LLM_PROVIDER` in `.env` (default "anthropic").
Providers are registered on startup only if their API key is present — so you
can run with only a Gemini key, only a Claude key, or both.

Usage:
    llm = get_llm()
    data = await llm.complete_json(system, user)                 # default provider
    data = await llm.complete_json(system, user, provider="gemini")  # explicit

Adding another provider:
    class MyProvider(BaseLLMProvider):
        name = "myprovider"
        async def complete(self, system, user, **kw): ...
    get_llm_manager().register(MyProvider(...))
"""
from __future__ import annotations

from typing import Any

import structlog

from backend.config import get_settings
from backend.services.llm.anthropic_provider import AnthropicProvider, DEFAULT_MODEL as ANTHROPIC_DEFAULT
from backend.services.llm.base import BaseLLMProvider, LLMResponse
from backend.services.llm.gemini_provider import GeminiProvider, DEFAULT_MODEL as GEMINI_DEFAULT

log = structlog.get_logger()


class LLMManager:
    def __init__(self, default_provider: str) -> None:
        self._providers: dict[str, BaseLLMProvider] = {}
        self._default = default_provider

    def register(self, provider: BaseLLMProvider) -> None:
        self._providers[provider.name] = provider
        log.info("llm.provider_registered", name=provider.name)

    def unregister(self, name: str) -> None:
        self._providers.pop(name, None)

    def available(self) -> list[str]:
        return list(self._providers.keys())

    def get(self, name: str | None = None) -> BaseLLMProvider:
        key = name or self._default
        if key not in self._providers:
            raise KeyError(
                f"LLM provider '{key}' not registered. Available: {self.available()}. "
                f"Check your .env API keys."
            )
        return self._providers[key]

    async def complete(
        self,
        system: str,
        user: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        json_mode: bool = False,
        **kwargs: Any,
    ) -> LLMResponse:
        return await self.get(provider).complete(system, user, model=model, json_mode=json_mode, **kwargs)

    async def complete_json(
        self,
        system: str,
        user: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return await self.get(provider).complete_json(system, user, model=model, **kwargs)


_manager: LLMManager | None = None


def get_llm_manager() -> LLMManager:
    """Singleton. Registers providers for whichever API keys are set in .env."""
    global _manager
    if _manager is not None:
        return _manager

    settings = get_settings()
    active = settings.llm_provider.lower()
    mgr = LLMManager(default_provider=active)

    # The active provider uses LLM_MODEL from env; inactive providers use their
    # hardcoded per-provider default so cross-provider calls still work.
    if settings.anthropic_api_key:
        model = settings.llm_model if active == "anthropic" else ANTHROPIC_DEFAULT
        try:
            mgr.register(AnthropicProvider(api_key=settings.anthropic_api_key, default_model=model))
        except Exception as exc:  # noqa: BLE001
            log.warning("llm.register_failed", provider="anthropic", error=str(exc))

    if settings.gemini_api_key:
        model = settings.llm_model if active == "gemini" else GEMINI_DEFAULT
        try:
            mgr.register(GeminiProvider(api_key=settings.gemini_api_key, default_model=model))
        except Exception as exc:  # noqa: BLE001
            log.warning("llm.register_failed", provider="gemini", error=str(exc))

    if not mgr.available():
        raise RuntimeError(
            "No LLM provider registered. Set ANTHROPIC_API_KEY or GEMINI_API_KEY in .env."
        )
    if active not in mgr.available():
        raise RuntimeError(
            f"LLM_PROVIDER='{active}' but its API key is missing. "
            f"Available: {mgr.available()}. Fix .env."
        )

    _manager = mgr
    return mgr


def get_llm() -> LLMManager:
    return get_llm_manager()
