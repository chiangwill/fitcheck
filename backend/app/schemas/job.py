from datetime import datetime

from pydantic import BaseModel


class JobParseRequest(BaseModel):
    url: str


class JobResponse(BaseModel):
    id: int
    url: str
    title: str | None
    company: str | None
    raw_content: str | None
    parsed_json: dict | None
    embedding_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
