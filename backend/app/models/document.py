from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Document(Base):

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        unique=True
    )

    extension: Mapped[str] = mapped_column(
        String(20),
        index=True
    )

    mime_type: Mapped[str] = mapped_column(
        String(100)
    )

    size_bytes: Mapped[int] = mapped_column(Integer)

    file_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="uploaded"
    )

    extracted_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )