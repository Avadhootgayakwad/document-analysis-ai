import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.database import Base


def generate_id():
    return str(uuid.uuid4())


def utc_now():
    return datetime.now(timezone.utc)


class Conversation(Base):

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_id
    )

    title: Mapped[str] = mapped_column(
        String(255),
        default="New Conversation"
    )

    document_ids: Mapped[list] = mapped_column(
        JSON,
        default=list
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):

    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_id
    )

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id"),
        index=True
    )

    role: Mapped[str] = mapped_column(
        String(20)
    )

    content: Mapped[str] = mapped_column(
        Text
    )

    sources: Mapped[list] = mapped_column(
        JSON,
        default=list
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now
    )

    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages"
    )