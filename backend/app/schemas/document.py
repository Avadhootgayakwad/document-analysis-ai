from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):

    id: str
    filename: str
    extension: str
    mime_type: str
    size_bytes: int
    status: str
    error_message: str | None
    uploaded_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRename(BaseModel):

    filename: str = Field(
        min_length=1,
        max_length=255
    )


class DocumentStatistics(BaseModel):

    total_documents: int
    total_size_bytes: int
    processed_documents: int
    pending_documents: int
    failed_documents: int
    file_types: dict[str, int]