from __future__ import annotations

import json
from typing import Any

from backend.agents.base import BaseAgent
from backend.schemas.agent import AgentOutput


class ValidationAgent(BaseAgent):
    name = "validation"
    prompt_file = "validation.md"

    async def run(self, context: dict[str, Any]) -> AgentOutput:
        idea = context["idea"]
        research = context.get("research", {})
        ideation = context.get("ideation", {})
        script = context.get("script_writer", {})

        user = (
            f"Original idea: {idea}\n\n"
            f"Research summary: {research.get('summary', '')}\n"
            f"Chosen angle: {json.dumps(ideation.get('chosen_angle', {}))}\n"
            f"Hook: {script.get('hook', '')}\n"
            f"Script (truncated): {str(script.get('script', ''))[:3000]}\n\n"
            "Score each on 1-10: clarity, engagement, seo_fit, virality, retention_risk. "
            "Then decide: approve OR request changes. If changes, specify which agent to loop back to "
            "(ideation | script_writer) and give actionable feedback.\n\n"
            "Return JSON: scores (object), overall (float 1-10), decision ('approve'|'revise'), "
            "loop_back_to (string, empty if approved), feedback (string), strengths (list), weaknesses (list)."
        )
        data = await self._llm_json(user)
        decision = data.get("decision", "approve")
        return AgentOutput(
            agent=self.name,
            data=data,
            confidence=float(data.get("overall", 7)) / 10,
            feedback_requested=decision == "revise",
            feedback_target=data.get("loop_back_to", ""),
            feedback_note=data.get("feedback", ""),
        )
