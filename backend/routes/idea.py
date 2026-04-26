from fastapi import APIRouter

from backend.orchestrator.pipeline import run_pipeline
from backend.schemas.idea import IdeaResponse, IdeaSubmission

router = APIRouter(prefix="/idea", tags=["idea"])


@router.post("/submit", response_model=IdeaResponse)
async def submit_idea(body: IdeaSubmission) -> IdeaResponse:
    run_id = await run_pipeline(
        idea=body.idea,
        niche=body.niche,
        target_length_minutes=body.target_length_minutes,
        tone=body.tone,
    )
    return IdeaResponse(run_id=run_id, status="queued")
