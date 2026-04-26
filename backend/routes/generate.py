"""Finalize a run and return the exportable scripts.

The pipeline produces the video script, voiceover narration, and per-scene visual
prompts as text. This endpoint assembles them into downloadable formats (JSON +
Markdown). No external TTS or video-gen providers are called — the user feeds
the scripts into the tool of their choice.
"""
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.orchestrator.pipeline import get_run
from backend.schemas.output import FinalOutput, MediaAssets, SceneBreakdown

router = APIRouter(prefix="/generate", tags=["generate"])


class ApprovalBody(BaseModel):
    run_id: str


@router.post("/final")
async def generate_final(body: ApprovalBody) -> dict:
    run = await get_run(body.run_id)
    if run is None:
        raise HTTPException(404, "run not found")
    if run.status != "awaiting_approval":
        raise HTTPException(400, f"run in state '{run.status}', cannot finalize")

    outputs = json.loads(run.result_json or "{}")
    media = outputs.get("media_generation", {}) or {}
    opt = outputs.get("optimization", {}) or {}
    script = outputs.get("script_writer", {}) or {}

    scenes = [SceneBreakdown(**s) for s in media.get("scenes", []) if isinstance(s, dict)]
    media_assets = MediaAssets(
        voiceover_script=media.get("voiceover_script", script.get("script", "")),
        scenes=scenes,
        thumbnail_prompts=media.get("thumbnail_prompts", []),
    )
    final = FinalOutput(
        run_id=run.id,
        title=opt.get("title", ""),
        description=opt.get("description", ""),
        tags=opt.get("tags", []),
        hook=script.get("hook", ""),
        script=script.get("script", ""),
        media=media_assets,
    )
    return {
        "final": final.model_dump(),
        "exports": {
            "voiceover_txt": media_assets.voiceover_script,
            "video_script_md": _render_video_script_md(final),
            "scenes_json": [s.model_dump() for s in scenes],
        },
    }


def _render_video_script_md(f: FinalOutput) -> str:
    lines = [
        f"# {f.title}",
        "",
        f"**Hook:** {f.hook}",
        "",
        "## Description",
        f.description,
        "",
        f"**Tags:** {', '.join(f.tags)}",
        "",
        "## Full script",
        f.script,
        "",
        "## Scene breakdown",
    ]
    for s in f.media.scenes:
        lines += [
            f"### Scene {s.index} — {s.duration_seconds}s",
            f"**Narration:** {s.narration}",
            f"**Visual prompt:** {s.visual_prompt}",
        ]
        if s.on_screen_text:
            lines.append(f"**On-screen text:** {s.on_screen_text}")
        lines.append("")
    if f.media.thumbnail_prompts:
        lines += ["## Thumbnail prompts", *[f"- {p}" for p in f.media.thumbnail_prompts]]
    return "\n".join(lines)
