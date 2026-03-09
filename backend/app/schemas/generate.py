from pydantic import BaseModel
from typing import Literal


class GenerateRequest(BaseModel):
    tone: Literal["正式", "活潑"] = "正式"
