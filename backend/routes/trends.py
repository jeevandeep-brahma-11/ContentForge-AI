import json

from fastapi import APIRouter
from sqlalchemy import select

from backend.database import SessionLocal, TrendSnapshot
from backend.workers.trends_worker import refresh_trends

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("")
async def list_trends(limit: int = 20) -> dict:
    async with SessionLocal() as s:
        rows = await s.execute(
            select(TrendSnapshot).order_by(TrendSnapshot.created_at.desc()).limit(limit)
        )
        snapshots = list(rows.scalars().all())
    return {
        "snapshots": [
            {
                "id": r.id,
                "niche": r.niche,
                "payload": json.loads(r.payload_json or "{}"),
                "created_at": r.created_at.isoformat(),
            }
            for r in snapshots
        ]
    }


@router.post("/refresh")
async def trigger_refresh() -> dict:
    """Run the trends worker once, out-of-band, in the backend's event loop."""
    await refresh_trends()
    return {"ok": True}
