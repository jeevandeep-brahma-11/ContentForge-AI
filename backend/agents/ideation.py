from __future__ import annotations

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.schemas.agent import AgentOutput


class IdeationAgent(BaseAgent):
    name = "ideation"
    prompt_file = "ideation.md"

    async def run(self, context: dict[str, Any]) -> AgentOutput:
        idea = context["idea"]
        research = context.get("research", {})
        feedback = context.get("feedback_note", "")

        user = (
            f"Original idea: {idea}\n\n"
            f"Research insights:\n{json.dumps(research)[:3000]}\n\n"
            + (f"Reviewer feedback to address:\n{feedback}\n\n" if feedback else "")
            + "Return JSON with: "
            "angles (list of 5 distinct video angles, each with title/hook/premise), "
            "chosen_angle (object: title, hook, premise, why_it_wins), "
            "target_audience (string), tone (string)."
        )
        data = await self._llm_json(user)
        return AgentOutput(agent=self.name, data=data, confidence=0.82)
