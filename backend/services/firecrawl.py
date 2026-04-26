"""Firecrawl wrapper for trend + competitor research."""
from __future__ import annotations

from typing import Any

import httpx
import structlog

from backend.config import get_settings

log = structlog.get_logger()

FIRECRAWL_BASE = "https://api.firecrawl.dev/v1"


class FirecrawlClient:
    def __init__(self) -> None:
        self.api_key = get_settings().firecrawl_api_key

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        if not self.api_key:
            log.warning("firecrawl.no_key", query=query)
            return _stub_results(query, limit)
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{FIRECRAWL_BASE}/search",
                headers=self._headers,
                json={"query": query, "limit": limit},
            )
            resp.raise_for_status()
            return resp.json().get("data", [])

    async def scrape(self, url: str) -> dict[str, Any]:
        if not self.api_key:
            return {"url": url, "markdown": "", "stubbed": True}
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{FIRECRAWL_BASE}/scrape",
                headers=self._headers,
                json={"url": url, "formats": ["markdown"]},
            )
            resp.raise_for_status()
            return resp.json().get("data", {})


def _stub_results(query: str, limit: int) -> list[dict[str, Any]]:
    return [
        {
            "title": f"[stub] Top trending result for '{query}' #{i}",
            "url": f"https://example.com/{i}",
            "description": "Firecrawl key not configured — returning placeholder.",
        }
        for i in range(1, limit + 1)
    ]


_client: FirecrawlClient | None = None


def get_firecrawl() -> FirecrawlClient:
    global _client
    if _client is None:
        _client = FirecrawlClient()
    return _client
