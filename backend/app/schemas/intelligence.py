from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):

    question: str = Field(
        min_length=1,
        max_length=5000
    )

    document_ids: list[str] = Field(
        min_length=1,
        max_length=20
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10
    )


class RetrievalResult(BaseModel):

    document_id: str
    filename: str
    chunk_index: int
    content: str
    relevance_score: float


class RetrievalResponse(BaseModel):

    question: str
    total_results: int
    results: list[RetrievalResult]
    context: str