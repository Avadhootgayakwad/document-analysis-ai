import logging

from sqlalchemy.orm import Session

from app.core.config import UPLOAD_DIR
from app.services.document_service import get_document
from app.services.extraction_service import extract_document


logger = logging.getLogger(__name__)


def process_document(
    document_id: str,
    db: Session
):

    document = get_document(document_id, db)

    document.status = "processing"
    document.error_message = None

    db.commit()

    try:

        file_path = UPLOAD_DIR / document.stored_filename

        text = extract_document(file_path)

        document.extracted_text = text
        document.status = "processed"
        document.error_message = None

        db.commit()
        db.refresh(document)

    except Exception as error:

        db.rollback()

        logger.exception(
            "Document processing failed: %s",
            document_id
        )

        document.status = "failed"
        document.extracted_text = None
        document.error_message = str(error)[:500]

        db.commit()
        db.refresh(document)

    return document