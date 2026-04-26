from pydantic import BaseModel, Field


class SceneBreakdown(BaseModel):
    index: int
    narration: str
    visual_prompt: str
    duration_seconds: float
    on_screen_text: str = ""


class MediaAssets(BaseModel):
    voiceover_script: str
    scenes: list[SceneBreakdown]
    thumbnail_prompts: list[str] = Field(default_factory=list)


class FinalOutput(BaseModel):
    run_id: str
    title: str
    description: str
    tags: list[str]
    hook: str
    script: str
    media: MediaAssets
