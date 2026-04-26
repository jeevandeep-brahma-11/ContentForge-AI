from __future__ import annotations

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.schemas.agent import AgentOutput


class ScriptWriterAgent(BaseAgent):
    name = "script_writer"
    prompt_file = "script.md"

    async def run(self, context: dict[str, Any]) -> AgentOutput:
        idea = context["idea"]
        ideation = context.get("ideation", {})
        target_min = context.get("target_length_minutes", 8)
        feedback = context.get("feedback_note", "")

        user = (
            f"Original idea: {idea}\n"
            f"Target length: ~{target_min} minutes (~{target_min * 150} words)\n\n"
            f"Chosen angle:\n{json.dumps(ideation.get('chosen_angle', {}))}\n"
            f"Audience: {ideation.get('target_audience', '')}\n"
            f"Tone: {ideation.get('tone', 'engaging')}\n\n"
            + (f"Reviewer feedback to address:\n{feedback}\n\n" if feedback else "")
            + "Write a high-retention YouTube script using hook → curiosity → payoff. "
            "Return JSON with: hook (string, <=15s spoken), script (full narration, plain prose), "
            "sections (list of {title, content}), cta (string)."
        )
        data = await self._llm_json(user)
        return AgentOutput(agent=self.name, data=data, confidence=0.8)
