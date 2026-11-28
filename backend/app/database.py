from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import DATABASE_DIR


DATABASE_PATH = DATABASE_DIR / "documind.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

def init_db():

    from app.models.document import Document
    from app.models.chat import Conversation, ChatMessage
    from app.models.summary import Summary
    from app.models.note import Note

    Base.metadata.create_all(bind=engine)