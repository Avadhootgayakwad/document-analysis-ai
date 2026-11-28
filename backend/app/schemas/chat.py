from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field
)


class ConversationCreate(BaseModel):

    title: str = Field(
        default="New Conversation",
        min_length=1,
        max_length=255
    )

    document_ids: list[str] = Field(
        min_length=1,
        max_length=20
    )


class ConversationRename(BaseModel):

    title: str = Field(
        min_length=1,
        max_length=255
    )


class ChatRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=4000
    )


class SourceResponse(BaseModel):

    source_number: int
    document_id: str
    filename: str
    chunk_index: int
    relevance_score: float
    excerpt: str


class MessageResponse(BaseModel):

    id: str
    conversation_id: str
    role: str
    content: str
    sources: list[SourceResponse]
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ConversationResponse(BaseModel):

    id: str
    title: str
    document_ids: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class ConversationDetail(ConversationResponse):

    messages: list[MessageResponse]


class ChatResponse(BaseModel):

    conversation_id: str
    message: MessageResponse