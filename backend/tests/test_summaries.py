import uuid

import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.document import Document
from app.services.llm_service import llm_service


@pytest.fixture
def client(tmp_path, monkeypatch):

    engine = create_engine(
        f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        connect_args={"check_same_thread": False}
    )

    TestingSession = sessionmaker(
        bind=engine,
        expire_on_commit=False
    )

    Base.metadata.create_all(engine)

    document_ids = []

    with TestingSession() as db:

        for index in range(2):

            document_id = str(uuid.uuid4())

            document_ids.append(document_id)

            db.add(
                Document(
                    id=document_id,
                    filename=f"business-{index}.txt",
                    stored_filename=f"business-{index}.txt",
                    extension=".txt",
                    mime_type="text/plain",
                    size_bytes=100,
                    file_hash=f"summary-test-{index}",
                    status="processed",
                    extracted_text=(
                        "Annual revenue is 2500000 INR. "
                        "Customer satisfaction is 92 percent."
                    )
                )
            )

        db.commit()

    def override_get_db():

        with TestingSession() as db:
            yield db

    async def fake_generate(*args, **kwargs):

        return "Business revenue is 2500000 INR."

    async def fake_model():

        return "test-model"

    monkeypatch.setattr(
        "app.main.init_db",
        lambda: None
    )

    monkeypatch.setattr(
        llm_service,
        "generate",
        fake_generate
    )

    monkeypatch.setattr(
        llm_service,
        "resolve_model",
        fake_model
    )

    app.dependency_overrides[get_db] = override_get_db

    try:

        with TestClient(app) as test_client:

            test_client.document_ids = document_ids

            yield test_client

    finally:

        app.dependency_overrides.clear()
        engine.dispose()


def generate(client, **kwargs):

    payload = {
        "document_ids": client.document_ids,
        "summary_type": "brief"
    }

    payload.update(kwargs)

    return client.post(
        "/api/summaries/generate",
        json=payload
    )


def test_generate_summary(client):

    response = generate(client)

    assert response.status_code == 200
    assert response.json()["cached"] is False


def test_single_document_summary(client):

    response = generate(
        client,
        document_ids=[client.document_ids[0]]
    )

    assert response.status_code == 200
    assert len(
        response.json()["summary"]["document_ids"]
    ) == 1


def test_summary_cache(client):

    first = generate(client).json()
    second = generate(client).json()

    assert second["cached"] is True

    assert (
        first["summary"]["id"]
        == second["summary"]["id"]
    )


def test_force_refresh(client):

    first = generate(client).json()

    second = generate(
        client,
        force_refresh=True
    ).json()

    assert second["cached"] is False

    assert (
        first["summary"]["id"]
        == second["summary"]["id"]
    )


@pytest.mark.parametrize(
    "summary_type",
    ["brief", "detailed", "executive", "key_findings"]
)
def test_summary_types(client, summary_type):

    response = generate(
        client,
        summary_type=summary_type
    )

    assert response.status_code == 200


def test_invalid_document(client):

    response = generate(
        client,
        document_ids=["invalid-id"]
    )

    assert response.status_code == 404


def test_list_summaries(client):

    generate(client)

    response = client.get("/api/summaries/")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_export_summary(client):

    summary = generate(client).json()["summary"]

    response = client.get(
        f"/api/summaries/{summary['id']}/export"
    )

    assert response.status_code == 200
    assert response.json()["id"] == summary["id"]


def test_delete_summary(client):

    summary = generate(client).json()["summary"]

    response = client.delete(
        f"/api/summaries/{summary['id']}"
    )

    assert response.status_code == 200

    response = client.get(
        f"/api/summaries/{summary['id']}"
    )

    assert response.status_code == 404