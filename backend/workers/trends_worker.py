"""Background trends researcher.

Runs on an interval. Per niche, makes ONE Firecrawl search and one Gemini parse
to produce a structured list of topics sorted by trendiness — biased toward
what American viewers actually watch. Designed to be cheap on Firecrawl's free
tier (1 query per niche per cycle, not 3)."""
from __future__ import annotations

import json

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.config import get_settings
from backend.database import SessionLocal, TrendSnapshot
from backend.services.firecrawl import get_firecrawl
from backend.services.llm import get_llm

log = structlog.get_logger()
_scheduler: AsyncIOScheduler | None = None

_PARSE_SYSTEM = (
    "You parse raw web search results about YouTube trends and return a clean "
    "structured list of topics, genres, and length hints. Output valid JSON only."
)


async def refresh_trends() -> None:
    settings = get_settings()
    fc = get_firecrawl()
    llm = get_llm()

    for niche in settings.niches:
        try:
            results = await fc.search(
                f"most watched YouTube genres USA trending {niche}",
                limit=10,
            )
            user = (
                f"Niche: {niche}\n"
                f"Raw web search results (JSON):\n{json.dumps(results)[:5000]}\n\n"
                "Extract a list of trending topics for this niche focused on the "
                "American YouTube audience. Return JSON:\n"
                "{\n"
                '  "items": [\n'
                "    {\n"
                '      "rank": int (1 = most trending),\n'
                '      "topic": string,\n'
                '      "genre": string,\n'
                '      "typical_length_min": int,\n'
                '      "trend_score": int (1-10),\n'
                '      "us_viewership": "low" | "medium" | "high",\n'
                '      "why_trending": string\n'
                "    }\n"
                "  ]\n"
                "}\n"
                "Sort items by trend_score DESCENDING. 8-12 items. If raw results are "
                "thin, supplement from general knowledge of current US YouTube trends."
            )
            parsed = await llm.complete_json(_PARSE_SYSTEM, user)
            items = parsed.get("items", [])
            # Defensive re-sort in case the model didn't.
            items.sort(key=lambda x: x.get("trend_score", 0), reverse=True)
            payload = {"niche": niche, "items": items, "raw": results}

            async with SessionLocal() as s:
                s.add(TrendSnapshot(niche=niche, payload_json=json.dumps(payload)))
                await s.commit()
            log.info("trends.refreshed", niche=niche, items=len(items))
        except Exception as exc:  # noqa: BLE001
            log.error("trends.refresh_failed", niche=niche, error=str(exc))


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    settings = get_settings()
    sched = AsyncIOScheduler()
    sched.add_job(refresh_trends, "interval", minutes=settings.trends_refresh_minutes, next_run_time=None)
    sched.start()
    _scheduler = sched
    log.info("trends.scheduler_started", minutes=settings.trends_refresh_minutes)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
