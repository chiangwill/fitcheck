from datetime import datetime

from pydantic import BaseModel


class MatchResponse(BaseModel):
    id: int
    resume_id: int
    job_id: int
    score: float | None
    matched_skills: list | None
    missing_skills: list | None
    suggestion: str | None
    cover_letter: str | None
    cover_letter_en: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
