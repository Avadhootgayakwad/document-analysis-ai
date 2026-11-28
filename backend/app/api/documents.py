from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    Query
)

from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.core.config import UPLOAD_DIR

from app.schemas.document import (
    DocumentResponse,
    DocumentRename,
    DocumentStatistics
)

from app.services import document_service


from fastapi import BackgroundTasks
from app.database import SessionLocal
from app.services.processing_service import process_document


router = APIRouter(
    prefix="/api/documents",
    tags=["Document Management"]
)


def process_uploaded_document(document_id: str):

    with SessionLocal() as db:

        process_document(document_id, db)

@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=201
)
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    document = await document_service.upload_document(
        file,
        db
    )

    background_tasks.add_task(
        process_uploaded_document,
        document.id
    )

    return document

@router.post("/upload-multiple")
async def upload_multiple(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):

    uploaded = []
    failed = []

    for file in files:

        try:

            document = await document_service.upload_document(
                file,
                db
            )

            background_tasks.add_task(
                process_uploaded_document,
                document.id
            )

            uploaded.append(
                DocumentResponse.model_validate(
                    document
                ).model_dump(mode="json")
            )

        except HTTPException as error:

            failed.append({
                "filename": file.filename,
                "error": error.detail
            })

    return {
        "uploaded_count": len(uploaded),
        "failed_count": len(failed),
        "uploaded": uploaded,
        "failed": failed
    }

@router.get(
    "/",
    response_model=list[DocumentResponse]
)
def documents(
    search: str = "",
    extension: str = "",
    status: str = "",
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):

    return document_service.list_documents(
        db=db,
        search=search,
        extension=extension,
        status=status,
        limit=limit,
        offset=offset
    )


@router.get(
    "/statistics",
    response_model=DocumentStatistics
)
def statistics(
    db: Session = Depends(get_db)
):

    return document_service.get_statistics(db)


@router.get(
    "/{document_id}",
    response_model=DocumentResponse
)
def document_details(
    document_id: str,
    db: Session = Depends(get_db)
):

    return document_service.get_document(
        document_id,
        db
    )


@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    db: Session = Depends(get_db)
):

    document = document_service.get_document(
        document_id,
        db
    )

    file_path = UPLOAD_DIR / document.stored_filename

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Stored file is missing."
        )

    return FileResponse(
        path=file_path,
        filename=document.filename,
        media_type="application/octet-stream"
    )


@router.patch(
    "/{document_id}/rename",
    response_model=DocumentResponse
)
def rename(
    document_id: str,
    payload: DocumentRename,
    db: Session = Depends(get_db)
):

    return document_service.rename_document(
        document_id,
        payload.filename,
        db
    )


@router.delete("/{document_id}")
def delete(
    document_id: str,
    db: Session = Depends(get_db)
):

    return document_service.delete_document(
        document_id,
        db
    )