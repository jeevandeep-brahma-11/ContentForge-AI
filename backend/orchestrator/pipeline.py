"""LangGraph-orchestrated agent pipeline with feedback loops.

Graph:

    START -> research -> ideation -> script_writer -> validation
                              ^           ^              |
                              |           +------+       |  (conditional)
                              +------------------+       v
                                                 optimization -> media_generation -> END

The validation node inspects the reviewer's decision and, if revision is
requested AND we are under `max_feedback_loops`, routes back to ideation or
script_writer with feedback_note attached. Otherwise it proceeds to optimization.

Why LangGraph: makes parallel/fan-out nodes trivial later — add a node, add its
edges. Agents themselves stay unchanged (`async def run(context) -> AgentOutput`).
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, TypedDict

import structlog
from langgraph.graph import END, StateGraph
from sqlalchemy import select

from backend.agents import (
    IdeationAgent,
    MediaGenerationAgent,
    OptimizationAgent,
    ResearchAgent,
    ScriptWriterAgent,
    ValidationAgent,
)
from backend.config import get_settings
from backend.database import PipelineRun, SessionLocal
from backend.schemas.agent import AgentLog

log = structlog.get_logger()


class PipelineState(TypedDict, total=False):
    run_id: str
    idea: str
    niche: str
    target_length_minutes: int
    tone: str
    research: dict[str, Any]
    ideation: dict[str, Any]
    script_writer: dict[str, Any]
    validation: dict[str, Any]
    optimization: dict[str, Any]
    media_generation: dict[str, Any]
    feedback_note: str
    loops: int
    max_loops: int
    revise_target: str
    logs: list[dict[str, Any]]


AGENTS_REGISTRY = {
    "research": ResearchAgent,
    "ideation": IdeationAgent,
    "script_writer": ScriptWriterAgent,
    "validation": ValidationAgent,
    "optimization": OptimizationAgent,
    "media_generation": MediaGenerationAgent,
}

_EPHEMERAL_KEYS = {"logs", "idea", "niche"}


async def _persist(state: PipelineState, status: str, current_agent: str) -> None:
    """Mirror the latest graph state into SQLite so the UI can poll progress."""
    run_id = state.get("run_id")
    if not run_id:
        return
    async with SessionLocal() as s:
        row = await s.get(PipelineRun, run_id)
        if row is None:
            return
        row.status = status
        row.current_agent = current_agent
        row.result_json = json.dumps(
            {k: v for k, v in state.items() if k not in _EPHEMERAL_KEYS},
            default=str,
        )
        row.logs_json = json.dumps(state.get("logs", []), default=str)
        row.updated_at = datetime.utcnow()
        await s.commit()


def _append_log(state: PipelineState, agent: str, event: str, message: str = "") -> list[dict[str, Any]]:
    entry = AgentLog(agent=agent, event=event, message=message).model_dump(mode="json")
    logs = list(state.get("logs", []))
    logs.append(entry)
    log.info("pipeline.event", run_id=state.get("run_id"), agent=agent, stage=event, message=message[:200])
    return logs


def _make_agent_node(name: str):
    agent_cls = AGENTS_REGISTRY[name]

    async def node(state: PipelineState) -> dict[str, Any]:
        start_logs = _append_log(state, name, "start")
        await _persist({**state, "logs": start_logs}, "running", name)
        try:
            out = await agent_cls().run(state)
        except Exception as exc:  # noqa: BLE001
            err_logs = _append_log({**state, "logs": start_logs}, name, "error", str(exc))
            await _persist({**state, "logs": err_logs}, "failed", "error")
            raise

        update: dict[str, Any] = {
            name: out.data,
            "logs": _append_log({**state, "logs": start_logs}, name, "complete", f"confidence={out.confidence:.2f}"),
        }

        if name == "validation":
            current_loops = state.get("loops", 0)
            max_loops = state.get("max_loops", 2)
            if out.feedback_requested and current_loops < max_loops:
                target = out.feedback_target if out.feedback_target in {"ideation", "script_writer"} else "script_writer"
                update["feedback_note"] = out.feedback_note
                update["loops"] = current_loops + 1
                update["revise_target"] = target
            else:
                update["feedback_note"] = ""
                update["revise_target"] = ""
        return update

    return node


def _route_after_validation(state: PipelineState) -> str:
    target = state.get("revise_target", "")
    if target in {"ideation", "script_writer"}:
        log.info("pipeline.loopback", target=target, loops=state.get("loops"))
        return target
    return "optimization"


def build_graph():
    g = StateGraph(PipelineState)
    for name in AGENTS_REGISTRY:
        g.add_node(name, _make_agent_node(name))
    g.set_entry_point("research")
    g.add_edge("research", "ideation")
    g.add_edge("ideation", "script_writer")
    g.add_edge("script_writer", "validation")
    g.add_conditional_edges(
        "validation",
        _route_after_validation,
        {
            "ideation": "ideation",
            "script_writer": "script_writer",
            "optimization": "optimization",
        },
    )
    g.add_edge("optimization", "media_generation")
    g.add_edge("media_generation", END)
    return g.compile()


GRAPH = build_graph()


async def _execute(initial: PipelineState) -> None:
    try:
        final_state: PipelineState = await GRAPH.ainvoke(initial)
        final_logs = _append_log(final_state, "orchestrator", "awaiting_approval")
        await _persist({**final_state, "logs": final_logs}, "awaiting_approval", "done")
    except Exception as exc:  # noqa: BLE001
        log.error("pipeline.failed", run_id=initial.get("run_id"), error=str(exc))


async def run_pipeline(
    idea: str,
    niche: str = "",
    target_length_minutes: int = 8,
    tone: str = "engaging",
) -> str:
    run_id = uuid.uuid4().hex
    async with SessionLocal() as s:
        s.add(PipelineRun(id=run_id, idea=idea, niche=niche, status="queued", current_agent=""))
        await s.commit()

    settings = get_settings()
    initial: PipelineState = {
        "run_id": run_id,
        "idea": idea,
        "niche": niche,
        "target_length_minutes": target_length_minutes,
        "tone": tone,
        "loops": 0,
        "max_loops": settings.max_feedback_loops,
        "feedback_note": "",
        "revise_target": "",
        "logs": [],
    }
    asyncio.create_task(_execute(initial))
    return run_id


async def get_run(run_id: str) -> PipelineRun | None:
    async with SessionLocal() as s:
        return await s.get(PipelineRun, run_id)


async def list_runs(limit: int = 20) -> list[PipelineRun]:
    async with SessionLocal() as s:
        result = await s.execute(
            select(PipelineRun).order_by(PipelineRun.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
