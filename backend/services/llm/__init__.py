"""LLM manager with pluggable providers. Claude and Gemini are built in."""
from backend.services.llm.anthropic_provider import AnthropicProvider
from backend.services.llm.base import BaseLLMProvider, LLMResponse
from backend.services.llm.gemini_provider import GeminiProvider
from backend.services.llm.manager import LLMManager, get_llm, get_llm_manager

__all__ = [
    "BaseLLMProvider",
    "LLMResponse",
    "LLMManager",
    "AnthropicProvider",
    "GeminiProvider",
    "get_llm",
    "get_llm_manager",
]
