import hashlib
import mimetypes
import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import UPLOAD_DIR, settings
from app.models.document import Document


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".doc",
    ".xlsx",
    ".xls",
    ".csv",
    ".txt",
    ".md",
    ".json"
}


def validate_filename(filename: str) -> str:

    filename = filename.strip()

    if (
        not filename
        or len(filename) > 255
        or filename in {".", ".."}
        or any(char in filename for char in '/\\:*?"<>|')
        or any(ord(char) < 32 for char in filename)
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename."
        )

    return filename


async def upload_document(
    file: UploadFile,
    db: Session
):

    filename = validate_filename(file.filename or "")
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {extension}"
        )

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    document_id = str(uuid.uuid4())
    stored_filename = f"{document_id}{extension}"
    file_path = UPLOAD_DIR / stored_filename

    file_hash = hashlib.sha256()
    size = 0

    try:

        with file_path.open("wb") as output:

            while chunk := await file.read(1024 * 1024):

                size += len(chunk)

                if size > max_size:
                    raise HTTPException(
                        status_code=413,
                        detail="File exceeds maximum upload size."
                    )

                file_hash.update(chunk)
                output.write(chunk)

        if size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty files are not allowed."
            )

        digest = file_hash.hexdigest()

        existing = db.scalar(
            select(Document).where(
                Document.file_hash == digest
            )
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate document: {existing.filename}"
            )

        document = Document(
            id=document_id,
            filename=filename,
            stored_filename=stored_filename,
            extension=extension,
            mime_type=(
                mimetypes.guess_type(filename)[0]
                or "application/octet-stream"
            ),
            size_bytes=size,
            file_hash=digest,
            status="uploaded"
        )

        db.add(document)
        db.commit()

        return document

    except IntegrityError:

        db.rollback()
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=409,
            detail="Document already exists."
        )

    except Exception:

        db.rollback()
        file_path.unlink(missing_ok=True)
        raise

    finally:

        await file.close()


def get_document(
    document_id: str,
    db: Session
):

    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    return document


def list_documents(
    db: Session,
    search: str = "",
    extension: str = "",
    status: str = "",
    limit: int = 100,
    offset: int = 0
):

    query = select(Document)

    if search:
        query = query.where(
            Document.filename.icontains(
                search,
                autoescape=True
            )
        )

    if extension:

        extension = "." + extension.lower().lstrip(".")

        query = query.where(
            Document.extension == extension
        )

    if status:
        query = query.where(
            Document.status == status
        )

    query = (
        query
        .order_by(Document.uploaded_at.desc())
        .offset(offset)
        .limit(limit)
    )

    return list(db.scalars(query).all())


def rename_document(
    document_id: str,
    new_filename: str,
    db: Session
):

    document = get_document(document_id, db)

    new_filename = validate_filename(new_filename)

    if Path(new_filename).suffix.lower() != document.extension:
        raise HTTPException(
            status_code=400,
            detail="File extension cannot be changed."
        )

    document.filename = new_filename

    db.commit()
    db.refresh(document)

    return document


def delete_document(
    document_id: str,
    db: Session
):

    document = get_document(document_id, db)

    file_path = UPLOAD_DIR / document.stored_filename

    db.delete(document)
    db.commit()

    file_path.unlink(missing_ok=True)

    return {
        "success": True,
        "message": "Document deleted successfully."
    }


def get_statistics(db: Session):

    documents = list(
        db.scalars(select(Document)).all()
    )

    file_types = {}

    for document in documents:

        extension = document.extension

        file_types[extension] = (
            file_types.get(extension, 0) + 1
        )

    return {
        "total_documents": len(documents),

        "total_size_bytes": sum(
            doc.size_bytes for doc in documents
        ),

        "processed_documents": sum(
            doc.status == "processed"
            for doc in documents
        ),

        "pending_documents": sum(
            doc.status in {"uploaded", "processing"}
            for doc in documents
        ),

        "failed_documents": sum(
            doc.status == "failed"
            for doc in documents
        ),

        "file_types": file_types
    }