import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.services import document_service



@pytest.fixture
def client(tmp_path, monkeypatch):

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()

    monkeypatch.setattr(
        document_service,
        "UPLOAD_DIR",
        upload_dir
    )

    monkeypatch.setattr(
        "app.api.documents.UPLOAD_DIR",
        upload_dir
    )

    monkeypatch.setattr(
        "app.main.init_db",
        lambda: None
    )

    engine = create_engine(
        f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        connect_args={"check_same_thread": False}
    )

    TestingSession = sessionmaker(
        bind=engine,
        expire_on_commit=False
    )

    # NEW: Use temporary database for background processing

    monkeypatch.setattr(
        "app.api.documents.SessionLocal",
        TestingSession
    )

    # NEW: Use temporary upload directory

    monkeypatch.setattr(
        "app.services.processing_service.UPLOAD_DIR",
        upload_dir
    )

    Base.metadata.create_all(engine)

    def override_get_db():

        db = TestingSession()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:

        with TestClient(app) as test_client:
            yield test_client

    finally:

        app.dependency_overrides.clear()
        engine.dispose()

def upload_sample(client):

    return client.post(
        "/api/documents/upload",
        files={
            "file": (
                "sample.txt",
                b"DocuMind AI test document.",
                "text/plain"
            )
        }
    )


def test_health(client):

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_upload(client):

    response = upload_sample(client)

    assert response.status_code == 201
    assert response.json()["filename"] == "sample.txt"


def test_duplicate_upload(client):

    upload_sample(client)

    response = upload_sample(client)

    assert response.status_code == 409


def test_invalid_extension(client):

    response = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "invalid.exe",
                b"test",
                "application/octet-stream"
            )
        }
    )

    assert response.status_code == 400


def test_empty_file(client):

    response = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "empty.txt",
                b"",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400


def test_list_documents(client):

    upload_sample(client)

    response = client.get("/api/documents/")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_search(client):

    upload_sample(client)

    response = client.get(
        "/api/documents/?search=sample"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_rename(client):

    document = upload_sample(client).json()

    response = client.patch(
        f"/api/documents/{document['id']}/rename",
        json={"filename": "renamed.txt"}
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "renamed.txt"


def test_download(client):

    document = upload_sample(client).json()

    response = client.get(
        f"/api/documents/{document['id']}/download"
    )

    assert response.status_code == 200
    assert response.content == b"DocuMind AI test document."


def test_delete(client):

    document = upload_sample(client).json()

    response = client.delete(
        f"/api/documents/{document['id']}"
    )

    assert response.status_code == 200

    response = client.get(
        f"/api/documents/{document['id']}"
    )

    assert response.status_code == 404


def test_statistics(client):

    upload_sample(client)

    response = client.get(
        "/api/documents/statistics"
    )

    assert response.status_code == 200
    assert response.json()["total_documents"] == 1


def test_multiple_upload(client):

    response = client.post(
        "/api/documents/upload-multiple",
        files=[
            ("files", ("one.txt", b"First document")),
            ("files", ("two.txt", b"Second document"))
        ]
    )

    assert response.status_code == 200
    assert response.json()["uploaded_count"] == 2