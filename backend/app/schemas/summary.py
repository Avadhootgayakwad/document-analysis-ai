from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SummaryType = Literal[
    "brief",
    "detailed",
    "executive",
    "key_findings"
]


class SummaryRequest(BaseModel):

    document_ids: list[str] = Field(
        min_length=1,
        max_length=20
    )

    summary_type: SummaryType = "brief"

    force_refresh: bool = False


class SummaryResponse(BaseModel):

    id: str
    document_ids: list[str]
    summary_type: str
    content: str
    model: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class SummaryResult(BaseModel):

    cached: bool
    summary: SummaryResponse