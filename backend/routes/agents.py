import json

from fastapi import APIRouter, HTTPException

from backend.database import PipelineRun, SessionLocal
from backend.orchestrator.pipeline import get_run, list_runs

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/status")
async def status(run_id: str | None = None) -> dict:
    if run_id:
        run = await get_run(run_id)
        if run is None:
            raise HTTPException(404, "run not found")
        return {
            "run_id": run.id,
            "idea": run.idea,
            "niche": run.niche,
            "status": run.status,
            "current_agent": run.current_agent,
            "outputs": json.loads(run.result_json or "{}"),
            "logs": json.loads(run.logs_json or "[]"),
            "updated_at": run.updated_at.isoformat(),
        }
    runs = await list_runs()
    return {
        "runs": [
            {
                "run_id": r.id,
                "idea": r.idea,
                "status": r.status,
                "current_agent": r.current_agent,
                "updated_at": r.updated_at.isoformat(),
            }
            for r in runs
        ]
    }


@router.delete("/run/{run_id}")
async def delete_run(run_id: str) -> dict:
    """Delete a single run (idea + all agent outputs + logs) from SQLite."""
    async with SessionLocal() as s:
        row = await s.get(PipelineRun, run_id)
        if row is None:
            raise HTTPException(404, "run not found")
        await s.delete(row)
        await s.commit()
    return {"deleted": run_id}
