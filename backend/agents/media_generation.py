from __future__ import annotations

from typing import Any

from backend.agents.base import BaseAgent
from backend.schemas.agent import AgentOutput


class MediaGenerationAgent(BaseAgent):
    name = "media_generation"
    prompt_file = "media.md"

    async def run(self, context: dict[str, Any]) -> AgentOutput:
        script = context.get("script_writer", {})
        optimization = context.get("optimization", {})
        target_min = context.get("target_length_minutes", 8)

        full_script = script.get("script", "")
        user = (
            f"Full narration script:\n{full_script[:6000]}\n\n"
            f"Title: {optimization.get('title', '')}\n"
            f"Target length: ~{target_min} minutes\n\n"
            "Break the script into sequential scenes. For each scene produce a cinematic "
            "visual prompt suitable for Gemini Video / Grok Imagine / Nano Banana. "
            "Produce a clean voiceover_script (narration only, no stage directions).\n\n"
            "Return JSON: voiceover_script (string), scenes (list of "
            "{index, narration, visual_prompt, duration_seconds, on_screen_text}), "
            "thumbnail_prompts (list of 3 image-gen prompts)."
        )
        data = await self._llm_json(user)
        return AgentOutput(agent=self.name, data=data, confidence=0.8)
