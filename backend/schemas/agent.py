from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentLog(BaseModel):
    agent: str
    event: str
    message: str = ""
    ts: datetime = Field(default_factory=datetime.utcnow)


class AgentOutput(BaseModel):
    agent: str
    data: dict[str, Any]
    confidence: float = 0.8
    feedback_requested: bool = False
    feedback_target: str = ""
    feedback_note: str = ""


class PipelineState(BaseModel):
    run_id: str
    idea: str
    status: str
    current_agent: str
    outputs: dict[str, Any] = Field(default_factory=dict)
    logs: list[AgentLog] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
