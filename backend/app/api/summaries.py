import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.summary import (
    SummaryRequest,
    SummaryResponse,
    SummaryResult
)

from app.services import summary_service
from app.services.llm_service import LLMServiceError


router = APIRouter(
    prefix="/api/summaries",
    tags=["AI Summaries"]
)


@router.post(
    "/generate",
    response_model=SummaryResult
)
async def generate(
    payload: SummaryRequest,
    db: Session = Depends(get_db)
):

    try:

        return await summary_service.generate_summary(
            payload.document_ids,
            payload.summary_type,
            payload.force_refresh,
            db
        )

    except LLMServiceError as error:

        raise HTTPException(
            status_code=503,
            detail=str(error)
        ) from error


@router.get(
    "/",
    response_model=list[SummaryResponse]
)
def list_summaries(
    db: Session = Depends(get_db)
):

    return summary_service.list_summaries(db)


@router.get(
    "/{summary_id}",
    response_model=SummaryResponse
)
def get_summary(
    summary_id: str,
    db: Session = Depends(get_db)
):

    return summary_service.get_summary(
        summary_id,
        db
    )


@router.delete("/{summary_id}")
def delete_summary(
    summary_id: str,
    db: Session = Depends(get_db)
):

    return summary_service.delete_summary(
        summary_id,
        db
    )


@router.get("/{summary_id}/export")
def export_summary(
    summary_id: str,
    db: Session = Depends(get_db)
):

    summary = summary_service.get_summary(
        summary_id,
        db
    )

    data = SummaryResponse.model_validate(
        summary
    ).model_dump(mode="json")

    return Response(
        content=json.dumps(
            data,
            indent=4,
            ensure_ascii=False
        ),
        media_type="application/json",
        headers={
            "Content-Disposition": (
                f'attachment; filename="summary-{summary_id}.json"'
            )
        }
    )