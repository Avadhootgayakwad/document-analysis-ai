import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Summary(Base):

    __tablename__ = "summaries"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    document_ids: Mapped[list] = mapped_column(JSON)

    summary_type: Mapped[str] = mapped_column(
        String(30)
    )

    content: Mapped[str] = mapped_column(Text)

    model: Mapped[str] = mapped_column(String(255))

    cache_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )