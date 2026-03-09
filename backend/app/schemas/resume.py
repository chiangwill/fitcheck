from datetime import datetime

from pydantic import BaseModel


class ResumeCreate(BaseModel):
    version_name: str
    raw_text: str


class ResumeResponse(BaseModel):
    id: int
    version_name: str
    raw_text: str
    parsed_json: dict | None
    embedding_id: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeUpdate(BaseModel):
    version_name: str | None = None
    raw_text: str | None = None
