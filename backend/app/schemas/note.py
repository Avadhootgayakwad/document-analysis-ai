from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):

    title: str = Field(
        min_length=1,
        max_length=255
    )

    content: str = Field(
        min_length=1,
        max_length=100000
    )

    category: str = Field(
        default="General",
        min_length=1,
        max_length=100
    )

    tags: list[str] = Field(
        default_factory=list,
        max_length=20
    )

    document_ids: list[str] = Field(
        default_factory=list,
        max_length=20
    )


class NoteUpdate(BaseModel):

    title: str = Field(
        min_length=1,
        max_length=255
    )

    content: str = Field(
        min_length=1,
        max_length=100000
    )

    category: str = Field(
        min_length=1,
        max_length=100
    )

    tags: list[str] = Field(
        default_factory=list,
        max_length=20
    )


class NoteGenerate(BaseModel):

    document_ids: list[str] = Field(
        min_length=1,
        max_length=20
    )

    title: str = Field(
        default="AI Generated Notes",
        min_length=1,
        max_length=255
    )

    category: str = Field(
        default="AI Insights",
        min_length=1,
        max_length=100
    )


class NoteResponse(BaseModel):

    id: str
    title: str
    content: str
    category: str
    tags: list[str]
    document_ids: list[str]
    source_type: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )