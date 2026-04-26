from __future__ import annotations

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.schemas.agent import AgentOutput


class OptimizationAgent(BaseAgent):
    name = "optimization"
    prompt_file = "optimization.md"

    async def run(self, context: dict[str, Any]) -> AgentOutput:
        research = context.get("research", {})
        ideation = context.get("ideation", {})
        script = context.get("script_writer", {})

        user = (
            f"Keywords: {research.get('target_keywords', [])}\n"
            f"Angle: {json.dumps(ideation.get('chosen_angle', {}))}\n"
            f"Hook: {script.get('hook', '')}\n"
            f"Script summary: {str(script.get('script', ''))[:1500]}\n\n"
            "Return JSON optimized for YouTube CTR + search: "
            "title (<=70 chars, curiosity-driven), "
            "description (150-250 words with keywords + timestamps placeholder + CTA), "
            "tags (list of 15-20 SEO tags), "
            "thumbnail_text_options (list of 4 short punchy options, <=5 words each), "
            "thumbnail_visual_concepts (list of 3 visual concept descriptions)."
        )
        data = await self._llm_json(user)
        return AgentOutput(agent=self.name, data=data, confidence=0.85)
