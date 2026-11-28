import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.note import (
    NoteCreate,
    NoteUpdate,
    NoteGenerate,
    NoteResponse
)

from app.services import note_service
from app.services.llm_service import LLMServiceError


router = APIRouter(
    prefix="/api/notes",
    tags=["Smart Notes"]
)


@router.post(
    "/",
    response_model=NoteResponse,
    status_code=201
)
def create(
    payload: NoteCreate,
    db: Session = Depends(get_db)
):

    return note_service.create_note(
        payload,
        db
    )


@router.post(
    "/generate",
    response_model=NoteResponse,
    status_code=201
)
async def generate(
    payload: NoteGenerate,
    db: Session = Depends(get_db)
):

    try:

        return await note_service.generate_ai_note(
            payload,
            db
        )

    except LLMServiceError as error:

        raise HTTPException(
            status_code=503,
            detail=str(error)
        ) from error


@router.get(
    "/",
    response_model=list[NoteResponse]
)
def list_notes(
    search: str = "",
    category: str = "",
    tag: str = "",
    db: Session = Depends(get_db)
):

    return note_service.list_notes(
        db,
        search,
        category,
        tag
    )


@router.get("/categories")
def categories(
    db: Session = Depends(get_db)
):

    return note_service.get_categories(db)


@router.get("/tags")
def tags(
    db: Session = Depends(get_db)
):

    return note_service.get_tags(db)


@router.get(
    "/{note_id}",
    response_model=NoteResponse
)
def get_note(
    note_id: str,
    db: Session = Depends(get_db)
):

    return note_service.get_note(
        note_id,
        db
    )


@router.put(
    "/{note_id}",
    response_model=NoteResponse
)
def update(
    note_id: str,
    payload: NoteUpdate,
    db: Session = Depends(get_db)
):

    return note_service.update_note(
        note_id,
        payload,
        db
    )


@router.delete("/{note_id}")
def delete(
    note_id: str,
    db: Session = Depends(get_db)
):

    return note_service.delete_note(
        note_id,
        db
    )


@router.get("/{note_id}/export")
def export_note(
    note_id: str,
    db: Session = Depends(get_db)
):

    note = note_service.get_note(
        note_id,
        db
    )

    data = NoteResponse.model_validate(
        note
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
                f'attachment; filename="note-{note_id}.json"'
            )
        }
    )