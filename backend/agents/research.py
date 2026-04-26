from __future__ import annotations

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.schemas.agent import AgentOutput
from backend.services.firecrawl import get_firecrawl


class ResearchAgent(BaseAgent):
    """Single Firecrawl search per run (free-tier friendly). Focused on what
    US viewers actually watch in this niche — topics, genre, typical length,
    trend direction. No SEO keyword search (we don't optimize for search yet)."""

    name = "research"
    prompt_file = "research.md"

    async def run(self, context: dict[str, Any]) -> AgentOutput:
        idea = context["idea"]
        niche = context.get("niche") or idea
        fc = get_firecrawl()

        results = await fc.search(
            f"most watched YouTube videos {niche} USA trending",
            limit=10,
        )

        user = (
            f"Video idea: {idea}\n"
            f"Niche: {niche}\n\n"
            f"Raw web search results (JSON):\n{json.dumps(results)[:6000]}\n\n"
            "Synthesize research from the raw results. Return JSON with:\n"
            "- trending_angles: list of angles, SORTED DESCENDING by current trendiness\n"
            "- genre_hints: list of genres/formats that are winning in this niche\n"
            "- typical_length_minutes: integer — what high-performing videos actually run\n"
            "- us_viewership_notes: brief string on American audience signals\n"
            "- audience_pain_points: list of viewer pain points\n"
            "- competitor_gaps: list of things top channels under-cover\n"
            "- summary: one-paragraph executive summary"
        )
        data = await self._llm_json(user)
        data["_raw_research"] = results
        return AgentOutput(agent=self.name, data=data, confidence=0.85)
