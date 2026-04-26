from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import structlog

from backend.schemas.agent import AgentOutput
from backend.services.llm import get_llm

log = structlog.get_logger()
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class BaseAgent(ABC):
    name: str = "base"
    prompt_file: str = ""

    def __init__(self) -> None:
        self.llm = get_llm()

    def load_prompt(self) -> str:
        if not self.prompt_file:
            return ""
        path = PROMPTS_DIR / self.prompt_file
        return path.read_text(encoding="utf-8") if path.exists() else ""

    @abstractmethod
    async def run(self, context: dict[str, Any]) -> AgentOutput:
        """Execute the agent. `context` carries prior agent outputs + original idea."""

    async def _llm_json(self, user_prompt: str) -> dict[str, Any]:
        system = self.load_prompt()
        log.info("agent.llm_call", agent=self.name, user_len=len(user_prompt))
        return await self.llm.complete_json(system, user_prompt)
