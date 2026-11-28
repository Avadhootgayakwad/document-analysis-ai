from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentResponse

from app.schemas.intelligence import (
    RetrievalRequest,
    RetrievalResponse
)

from app.services.document_service import get_document
from app.services.processing_service import process_document

from app.services.retrieval_service import (
    retrieve_context,
    build_context
)


router = APIRouter(
    prefix="/api/intelligence",
    tags=["Document Intelligence"]
)


@router.post(
    "/process/{document_id}",
    response_model=DocumentResponse
)
def process(
    document_id: str,
    db: Session = Depends(get_db)
):

    return process_document(document_id, db)


@router.post("/process-all")
def process_all(
    db: Session = Depends(get_db)
):

    documents = list(
        db.scalars(
            select(Document).where(
                Document.status.in_(
                    ["uploaded", "failed"]
                )
            )
        ).all()
    )

    processed = 0
    failed = 0

    for document in documents:

        result = process_document(document.id, db)

        if result.status == "processed":
            processed += 1
        else:
            failed += 1

    return {
        "total": len(documents),
        "processed": processed,
        "failed": failed
    }


@router.get("/text/{document_id}")
def document_text(
    document_id: str,
    db: Session = Depends(get_db)
):

    document = get_document(document_id, db)

    if document.status != "processed":

        raise HTTPException(
            status_code=409,
            detail="Document has not been processed."
        )

    text = document.extracted_text or ""

    return {
        "document_id": document.id,
        "filename": document.filename,
        "character_count": len(text),
        "word_count": len(text.split()),
        "text": text
    }


@router.post(
    "/retrieve",
    response_model=RetrievalResponse
)
def retrieve(
    payload: RetrievalRequest,
    db: Session = Depends(get_db)
):

    documents = []

    for document_id in dict.fromkeys(payload.document_ids):

        document = get_document(document_id, db)

        if document.status != "processed":

            raise HTTPException(
                status_code=409,
                detail=(
                    f"{document.filename} "
                    "has not been processed."
                )
            )

        documents.append({
            "id": document.id,
            "filename": document.filename,
            "text": document.extracted_text
        })

    results = retrieve_context(
        question=payload.question,
        documents=documents,
        top_k=payload.top_k
    )

    return {
        "question": payload.question,
        "total_results": len(results),
        "results": results,
        "context": build_context(results)
    }