import uuid

import pytest

from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.document import Document
from app.services import chat_service


@pytest.fixture
def client(tmp_path, monkeypatch):

    engine = create_engine(
        f"sqlite:///{(tmp_path / 'chat_test.db').as_posix()}",
        connect_args={
            "check_same_thread": False
        }
    )

    TestingSession = sessionmaker(
        bind=engine,
        expire_on_commit=False
    )

    Base.metadata.create_all(engine)

    document_id = str(uuid.uuid4())

    with TestingSession() as db:

        document = Document(
            id=document_id,
            filename="business.txt",
            stored_filename="business.txt",
            extension=".txt",
            mime_type="text/plain",
            size_bytes=100,
            file_hash="test-business-hash",
            status="processed",
            extracted_text=(
                "TechNova annual revenue is "
                "2500000 INR. Customer satisfaction "
                "is 92 percent."
            )
        )

        db.add(document)
        db.commit()

    def override_get_db():

        with TestingSession() as db:
            yield db

    async def fake_generate(
        messages,
        **kwargs
    ):

        return (
            "The annual revenue is "
            "2500000 INR. [Source 1]"
        )

    async def fake_stream(
        messages,
        **kwargs
    ):

        yield "Annual revenue "
        yield "is 2500000 INR."

    async def fake_health():

        return {
            "connected": True,
            "provider": "LM Studio",
            "model": "test-model"
        }

    monkeypatch.setattr(
        "app.main.init_db",
        lambda: None
    )

    monkeypatch.setattr(
        "app.api.chat.SessionLocal",
        TestingSession
    )

    monkeypatch.setattr(
        chat_service.llm_service,
        "generate",
        fake_generate
    )

    monkeypatch.setattr(
        chat_service.llm_service,
        "stream",
        fake_stream
    )

    monkeypatch.setattr(
        chat_service.llm_service,
        "health",
        fake_health
    )

    app.dependency_overrides[get_db] = override_get_db

    try:

        with TestClient(app) as test_client:

            test_client.document_id = document_id

            yield test_client

    finally:

        app.dependency_overrides.clear()
        engine.dispose()


def create_conversation(client):

    response = client.post(
        "/api/chat/conversations",
        json={
            "title": "Business Analysis",
            "document_ids": [
                client.document_id
            ]
        }
    )

    assert response.status_code == 201

    return response.json()


def test_ai_health(client):

    response = client.get(
        "/api/chat/health"
    )

    assert response.status_code == 200
    assert response.json()["connected"] is True


def test_create_conversation(client):

    conversation = create_conversation(client)

    assert conversation["title"] == "Business Analysis"


def test_list_conversations(client):

    create_conversation(client)

    response = client.get(
        "/api/chat/conversations"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_invalid_document(client):

    response = client.post(
        "/api/chat/conversations",
        json={
            "title": "Invalid",
            "document_ids": ["invalid-id"]
        }
    )

    assert response.status_code == 404


def test_ask_question(client):

    conversation = create_conversation(client)

    response = client.post(
        f"/api/chat/conversations/{conversation['id']}/ask",
        json={
            "question": "What is the annual revenue?"
        }
    )

    assert response.status_code == 200

    message = response.json()["message"]

    assert "2500000" in message["content"]
    assert len(message["sources"]) > 0


def test_chat_history(client):

    conversation = create_conversation(client)

    conversation_id = conversation["id"]

    client.post(
        f"/api/chat/conversations/{conversation_id}/ask",
        json={
            "question": "What is the revenue?"
        }
    )

    response = client.get(
        f"/api/chat/conversations/{conversation_id}"
    )

    assert response.status_code == 200
    assert len(response.json()["messages"]) == 2


def test_streaming(client):

    conversation = create_conversation(client)

    response = client.post(
        f"/api/chat/conversations/{conversation['id']}/stream",
        json={
            "question": "What is the annual revenue?"
        }
    )

    assert response.status_code == 200

    assert "text/event-stream" in (
        response.headers["content-type"]
    )

    assert '"type": "token"' in response.text
    assert '"type": "done"' in response.text

    history = client.get(
        f"/api/chat/conversations/{conversation['id']}"
    ).json()["messages"]

    assert len(history) == 2

    assert history[-1]["content"] == (
        "Annual revenue is 2500000 INR."
    )


def test_rename_conversation(client):

    conversation = create_conversation(client)

    response = client.patch(
        f"/api/chat/conversations/{conversation['id']}",
        json={
            "title": "Updated Business Analysis"
        }
    )

    assert response.status_code == 200

    assert response.json()["title"] == (
        "Updated Business Analysis"
    )


def test_export_conversation(client):

    conversation = create_conversation(client)

    response = client.get(
        f"/api/chat/conversations/{conversation['id']}/export"
    )

    assert response.status_code == 200

    assert "attachment" in (
        response.headers["content-disposition"]
    )

    assert response.json()["id"] == conversation["id"]


def test_delete_conversation(client):

    conversation = create_conversation(client)

    response = client.delete(
        f"/api/chat/conversations/{conversation['id']}"
    )

    assert response.status_code == 200

    response = client.get(
        f"/api/chat/conversations/{conversation['id']}"
    )

    assert response.status_code == 404


def test_no_relevant_context(client):

    conversation = create_conversation(client)

    response = client.post(
        f"/api/chat/conversations/{conversation['id']}/ask",
        json={
            "question": "Neptune orbital period"
        }
    )

    assert response.status_code == 200

    message = response.json()["message"]

    assert message["sources"] == []

    assert "sufficient relevant information" in (
        message["content"]
    )