import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Note(Base):

    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    title: Mapped[str] = mapped_column(
        String(255)
    )

    content: Mapped[str] = mapped_column(Text)

    category: Mapped[str] = mapped_column(
        String(100),
        default="General",
        index=True
    )

    tags: Mapped[list] = mapped_column(
        JSON,
        default=list
    )

    document_ids: Mapped[list] = mapped_column(
        JSON,
        default=list
    )

    source_type: Mapped[str] = mapped_column(
        String(20),
        default="manual"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )