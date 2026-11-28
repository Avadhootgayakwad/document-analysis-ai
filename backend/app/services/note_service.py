from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.models.note import Note
from app.models.document import Document

from app.services.summary_service import (
    generate_summary,
    summarize_text
)


def clean_tags(tags: list[str]):

    return list(
        dict.fromkeys(
            tag.strip().lower()[:50]
            for tag in tags
            if tag.strip()
        )
    )


def required_text(value: str, field: str):

    value = value.strip()

    if not value:

        raise HTTPException(
            status_code=400,
            detail=f"{field} cannot be empty."
        )

    return value


def create_note(
    payload,
    db: Session,
    source_type: str = "manual"
):

    document_ids = list(
        dict.fromkeys(payload.document_ids)
    )

    for document_id in document_ids:

        if not db.get(Document, document_id):

            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}"
            )

    note = Note(
        title=required_text(payload.title, "Title"),
        content=required_text(payload.content, "Content"),
        category=required_text(payload.category, "Category"),
        tags=clean_tags(payload.tags),
        document_ids=document_ids,
        source_type=source_type
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return note


def get_note(
    note_id: str,
    db: Session
):

    note = db.get(Note, note_id)

    if not note:

        raise HTTPException(
            status_code=404,
            detail="Note not found."
        )

    return note


def list_notes(
    db: Session,
    search: str = "",
    category: str = "",
    tag: str = ""
):

    query = select(Note)

    if search:

        query = query.where(
            or_(
                Note.title.icontains(
                    search,
                    autoescape=True
                ),
                Note.content.icontains(
                    search,
                    autoescape=True
                )
            )
        )

    if category:

        query = query.where(
            Note.category == category
        )

    notes = list(
        db.scalars(
            query.order_by(
                Note.updated_at.desc()
            )
        ).all()
    )

    if tag:

        tag = tag.strip().lower()

        notes = [
            note
            for note in notes
            if tag in note.tags
        ]

    return notes


def update_note(
    note_id: str,
    payload,
    db: Session
):

    note = get_note(note_id, db)

    note.title = required_text(
        payload.title, "Title"
    )

    note.content = required_text(
        payload.content, "Content"
    )

    note.category = required_text(
        payload.category, "Category"
    )

    note.tags = clean_tags(payload.tags)

    db.commit()
    db.refresh(note)

    return note


def delete_note(
    note_id: str,
    db: Session
):

    note = get_note(note_id, db)

    db.delete(note)
    db.commit()

    return {
        "success": True,
        "message": "Note deleted."
    }


async def generate_ai_note(
    payload,
    db: Session
):

    from app.schemas.note import NoteCreate

    result = await generate_summary(
        document_ids=payload.document_ids,
        summary_type="detailed",
        force_refresh=False,
        db=db
    )

    summary = result["summary"]

    content = await summarize_text(
        summary.content,
        (
            "Convert the supplied summary into structured "
            "Markdown notes using these headings:\n"
            "## Overview\n"
            "## Key Concepts\n"
            "## Important Facts\n"
            "## Key Findings\n"
            "## Action Items\n"
            "## Conclusion\n"
            "Do not invent unsupported information."
        ),
        max_tokens=512
    )

    if "Coverage notice:" in summary.content:

        content += (
            "\n\nCoverage notice:"
            + summary.content.split(
                "Coverage notice:", 1
            )[1]
        )

    note_payload = NoteCreate(
        title=payload.title,
        content=content,
        category=payload.category,
        tags=["ai-generated", "document-analysis"],
        document_ids=payload.document_ids
    )

    return create_note(
        note_payload,
        db,
        source_type="ai"
    )


def get_categories(db: Session):

    categories = db.scalars(
        select(Note.category).distinct()
    ).all()

    return sorted(categories)


def get_tags(db: Session):

    notes = db.scalars(
        select(Note)
    ).all()

    return sorted({
        tag
        for note in notes
        for tag in note.tags
    })