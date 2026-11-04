import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.models.base import Base
from app.models import user, document, permission
from app.routers import documents as documents_router


@pytest.fixture
def api(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    TestingSession = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(
        documents_router,
        "STORAGE_DIR",
        tmp_path / "uploads"
    )

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    yield client

    client.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def register_and_login(client, username, email):
    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "T3st!SecurePassw0rd"
        }
    )

    if response.status_code == 409:
        assert "already registered" in response.text

    else:
        assert response.status_code == 201, response.text

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "T3st!SecurePassw0rd"
        }
    )

    assert response.status_code == 200, response.text


def upload_pdf(client):
    return client.post(
        "/documents/upload",
        files={
            "file": (
                "sample.pdf",
                b"%PDF-1.4\nSecureDoc integration test",
                "application/pdf"
            )
        }
    )


def test_upload_and_download_document(api):
    register_and_login(api, "owner1", "owner1@example.com")

    upload_response = upload_pdf(api)
    assert upload_response.status_code == 201, upload_response.text

    document_id = upload_response.json()["document_id"]

    download_response = api.get(
        f"/documents/{document_id}/download"
    )

    assert download_response.status_code == 200
    assert download_response.content.startswith(b"%PDF-")


def test_grant_and_revoke_permission(api):
    register_and_login(api, "owner2", "owner2@example.com")

    upload_response = upload_pdf(api)
    assert upload_response.status_code == 201, upload_response.text
    document_id = upload_response.json()["document_id"]

    api.post("/auth/logout")

    register_and_login(api, "viewer2", "viewer2@example.com")
    viewer_id = api.get("/auth/me").json()["user_id"]

    api.post("/auth/logout")

    register_and_login(api, "owner2", "owner2@example.com")

    grant_response = api.post(
        f"/documents/{document_id}/permissions",
        json={
            "user_id": viewer_id,
            "access_level": "viewer"
        }
    )

    assert grant_response.status_code == 200, grant_response.text
    assert grant_response.json()["access_level"] == "viewer"

    api.post("/auth/logout")
    register_and_login(api, "viewer2", "viewer2@example.com")

    allowed_response = api.get(
        f"/documents/{document_id}/download"
    )
    assert allowed_response.status_code == 200

    api.post("/auth/logout")
    register_and_login(api, "owner2", "owner2@example.com")

    revoke_response = api.delete(
        f"/documents/{document_id}/permissions/{viewer_id}"
    )
    assert revoke_response.status_code == 200, revoke_response.text

    api.post("/auth/logout")
    register_and_login(api, "viewer2", "viewer2@example.com")

    denied_response = api.get(
        f"/documents/{document_id}/download"
    )
    assert denied_response.status_code == 403


def test_unauthenticated_document_access_is_rejected(api):
    response = api.get("/documents/")

    assert response.status_code == 401


def test_document_list_shows_owned_documents(api):
    register_and_login(api, "owner3", "owner3@example.com")

    upload_response = upload_pdf(api)
    assert upload_response.status_code == 201, upload_response.text

    response = api.get("/documents/")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["filename"] == "sample.pdf"
    assert response.json()[0]["is_owner"] is True
