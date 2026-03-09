from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ApplicationStatus = Literal["pending", "applied", "interviewing", "offer", "rejected"]


class ApplicationCreate(BaseModel):
    job_id: int
    match_id: int | None = None


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    notes: str | None = None
    applied_at: datetime | None = None


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    match_id: int | None
    status: str
    notes: str | None
    applied_at: datetime | None
    updated_at: datetime

    model_config = {"from_attributes": True}
