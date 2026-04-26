from pydantic import BaseModel, Field


class IdeaSubmission(BaseModel):
    idea: str = Field(..., min_length=4, description="The raw video idea or topic from the user")
    niche: str = Field(default="", description="Optional niche/category tag")
    target_length_minutes: int = Field(default=8, ge=1, le=60)
    tone: str = Field(default="engaging, conversational")


class IdeaResponse(BaseModel):
    run_id: str
    status: str
