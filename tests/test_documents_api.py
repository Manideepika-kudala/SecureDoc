import io
import zipfile

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
    client.get('/')
    csrf_token = client.cookies.get('csrf_token')
    client.headers.update({'X-CSRF-Token': csrf_token})

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
    assert "attachment" in download_response.headers["content-disposition"]
    assert download_response.headers["x-content-type-options"] == "nosniff"
    assert download_response.headers["cache-control"] == "private, no-store, max-age=0"
    assert download_response.headers["pragma"] == "no-cache"



def test_document_preview_returns_inline_pdf(api):
    register_and_login(api, "preview_owner", "preview_owner@example.com")

    upload_response = upload_pdf(api)
    assert upload_response.status_code == 201, upload_response.text

    document_id = upload_response.json()["document_id"]

    response = api.get(f"/documents/{document_id}/preview")

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.headers["content-disposition"] == "inline"
    assert response.headers["x-content-type-options"] == "nosniff"


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

    preview_response = api.get(
        f"/documents/{document_id}/preview"
    )
    assert preview_response.status_code == 200
    assert preview_response.headers["content-disposition"] == "inline"

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

    denied_preview = api.get(
        f"/documents/{document_id}/preview"
    )
    assert denied_preview.status_code == 403


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

def test_editor_permission_can_edit_text_document(api):
    register_and_login(api, "edit_owner", "edit_owner@example.com")

    upload_response = api.post(
        "/documents/upload",
        files={
            "file": (
                "notes.txt",
                b"Original content",
                "text/plain"
            )
        }
    )
    assert upload_response.status_code == 201, upload_response.text
    document_id = upload_response.json()["document_id"]

    api.post("/auth/logout")
    register_and_login(api, "edit_user", "edit_user@example.com")
    editor_id = api.get("/auth/me").json()["user_id"]

    api.post("/auth/logout")
    register_and_login(api, "view_user", "view_user@example.com")
    viewer_id = api.get("/auth/me").json()["user_id"]

    api.post("/auth/logout")
    register_and_login(api, "edit_owner", "edit_owner@example.com")

    editor_grant = api.post(
        f"/documents/{document_id}/permissions",
        json={"user_id": editor_id, "access_level": "editor"}
    )
    assert editor_grant.status_code == 200, editor_grant.text

    viewer_grant = api.post(
        f"/documents/{document_id}/permissions",
        json={"user_id": viewer_id, "access_level": "viewer"}
    )
    assert viewer_grant.status_code == 200, viewer_grant.text

    api.post("/auth/logout")
    register_and_login(api, "edit_user", "edit_user@example.com")

    edit_response = api.put(
        f"/documents/{document_id}/edit",
        json={"content": "Updated by editor"}
    )
    assert edit_response.status_code == 200, edit_response.text

    preview_response = api.get(
        f"/documents/{document_id}/preview"
    )
    assert preview_response.status_code == 200
    assert preview_response.content == b"Updated by editor"

    api.post("/auth/logout")
    register_and_login(api, "view_user", "view_user@example.com")

    denied_response = api.put(
        f"/documents/{document_id}/edit",
        json={"content": "Unauthorized change"}
    )
    assert denied_response.status_code == 403



def test_owner_can_replace_document_file(api):
    register_and_login(api, "replace_owner", "replace_owner@example.com")

    upload_response = upload_pdf(api)
    assert upload_response.status_code == 201, upload_response.text
    document_id = upload_response.json()["document_id"]

    replacement_content = b"%PDF-1.7\\nReplacement by owner"

    replace_response = api.put(
        f"/documents/{document_id}/replace",
        files={
            "file": (
                "replacement.pdf",
                replacement_content,
                "application/pdf"
            )
        }
    )

    assert replace_response.status_code == 200, replace_response.text
    assert replace_response.json()["document_id"] == document_id

    download_response = api.get(
        f"/documents/{document_id}/download"
    )

    assert download_response.status_code == 200
    assert download_response.content == replacement_content


def test_editor_can_replace_but_viewer_cannot(api):
    register_and_login(api, "replace_owner2", "replace_owner2@example.com")

    upload_response = upload_pdf(api)
    assert upload_response.status_code == 201, upload_response.text
    document_id = upload_response.json()["document_id"]

    api.post("/auth/logout")
    register_and_login(api, "replace_editor", "replace_editor@example.com")
    editor_id = api.get("/auth/me").json()["user_id"]

    api.post("/auth/logout")
    register_and_login(api, "replace_viewer", "replace_viewer@example.com")
    viewer_id = api.get("/auth/me").json()["user_id"]

    api.post("/auth/logout")
    register_and_login(api, "replace_owner2", "replace_owner2@example.com")

    editor_grant = api.post(
        f"/documents/{document_id}/permissions",
        json={"user_id": editor_id, "access_level": "editor"}
    )
    assert editor_grant.status_code == 200, editor_grant.text

    viewer_grant = api.post(
        f"/documents/{document_id}/permissions",
        json={"user_id": viewer_id, "access_level": "viewer"}
    )
    assert viewer_grant.status_code == 200, viewer_grant.text

    api.post("/auth/logout")
    register_and_login(api, "replace_editor", "replace_editor@example.com")

    replacement_content = b"%PDF-1.7\\nReplacement by editor"

    editor_response = api.put(
        f"/documents/{document_id}/replace",
        files={
            "file": (
                "replacement.pdf",
                replacement_content,
                "application/pdf"
            )
        }
    )

    assert editor_response.status_code == 200, editor_response.text

    api.post("/auth/logout")
    register_and_login(api, "replace_viewer", "replace_viewer@example.com")

    viewer_response = api.put(
        f"/documents/{document_id}/replace",
        files={
            "file": (
                "replacement.pdf",
                b"%PDF-1.7\\nUnauthorized replacement",
                "application/pdf"
            )
        }
    )

    assert viewer_response.status_code == 403

def test_login_rate_limit_blocks_after_five_failed_attempts(api):
    register_and_login(api, "rate_user", "rate_user@example.com")
    api.post("/auth/logout")

    for _ in range(5):
        response = api.post(
            "/auth/login",
            json={
                "email": "rate_user@example.com",
                "password": "WrongPassword123!"
            }
        )
        assert response.status_code == 401

    blocked_response = api.post(
        "/auth/login",
        json={
            "email": "rate_user@example.com",
            "password": "T3st!SecurePassw0rd"
        }
    )

    assert blocked_response.status_code == 429
    assert "Retry-After" in blocked_response.headers
    assert int(blocked_response.headers["Retry-After"]) > 0


def test_successful_login_resets_failed_attempts(api):
    register_and_login(api, "reset_user", "reset_user@example.com")
    api.post("/auth/logout")

    login_data = {
        "email": "reset_user@example.com",
        "password": "T3st!SecurePassw0rd"
    }

    wrong_data = {
        "email": "reset_user@example.com",
        "password": "WrongPassword123!"
    }

    for _ in range(4):
        response = api.post("/auth/login", json=wrong_data)
        assert response.status_code == 401

    success_response = api.post("/auth/login", json=login_data)
    assert success_response.status_code == 200

    api.post("/auth/logout")

    for _ in range(5):
        response = api.post("/auth/login", json=wrong_data)
        assert response.status_code == 401

    blocked_response = api.post("/auth/login", json=login_data)
    assert blocked_response.status_code == 429


def test_old_session_invalidated_after_session_version_change(api):
    from app.models.user import User

    register_and_login(api, "session_user", "session_user@example.com")

    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)

    try:
        test_user = db.query(User).filter_by(
            email="session_user@example.com"
        ).first()

        assert test_user is not None
        test_user.session_version += 1
        db.commit()
    finally:
        db_generator.close()

    response = api.get("/documents/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or inactive user session"


def test_auth_me_rejects_old_session_after_version_change(api):
    from app.models.user import User

    register_and_login(api, "me_session_user", "me_session_user@example.com")

    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)

    try:
        test_user = db.query(User).filter_by(
            email="me_session_user@example.com"
        ).first()

        assert test_user is not None
        test_user.session_version += 1
        db.commit()
    finally:
        db_generator.close()

    response = api.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or inactive user session"


def test_user_search_rejects_sql_injection_payload(api):
    register_and_login(api, "sql_owner", "sql_owner@example.com")

    upload_response = upload_pdf(api)
    assert upload_response.status_code == 201, upload_response.text

    document_id = upload_response.json()["document_id"]

    target_response = api.post(
        "/auth/register",
        json={
            "username": "normal_user",
            "email": "normal_user@example.com",
            "password": "T3st!SecurePassw0rd"
        }
    )
    assert target_response.status_code == 201, target_response.text

    response = api.get(
        f"/documents/{document_id}/users/search",
        params={"q": "' OR 1=1 --"}
    )

    assert response.status_code == 200, response.text
    assert response.json() == []

def test_owner_can_delete_document(api):
    register_and_login(api, "delete_owner", "delete_owner@example.com")

    upload_response = upload_pdf(api)
    assert upload_response.status_code == 201, upload_response.text
    document_id = upload_response.json()["document_id"]

    delete_response = api.delete(f"/documents/{document_id}")
    assert delete_response.status_code == 200, delete_response.text
    assert delete_response.json()["message"] == "Document deleted successfully"

    download_response = api.get(f"/documents/{document_id}/download")
    assert download_response.status_code == 404


def test_non_owner_cannot_delete_document(api):
    register_and_login(api, "delete_owner2", "delete_owner2@example.com")

    upload_response = upload_pdf(api)
    assert upload_response.status_code == 201, upload_response.text
    document_id = upload_response.json()["document_id"]

    api.post("/auth/logout")
    register_and_login(api, "delete_other", "delete_other@example.com")

    delete_response = api.delete(f"/documents/{document_id}")
    assert delete_response.status_code == 403

    api.post("/auth/logout")
    register_and_login(api, "delete_owner2", "delete_owner2@example.com")

    download_response = api.get(f"/documents/{document_id}/download")
    assert download_response.status_code == 200


def test_delete_missing_document_returns_404(api):
    register_and_login(api, "delete_missing", "delete_missing@example.com")

    response = api.delete("/documents/999999")
    assert response.status_code == 404

def test_document_listing_search_and_ownership_filter(api):
    register_and_login(api, "listing_owner", "listing_owner@example.com")

    first = upload_pdf(api)
    second = upload_pdf(api)
    assert first.status_code == 201
    assert second.status_code == 201

    all_response = api.get("/documents/")
    assert all_response.status_code == 200
    assert len(all_response.json()) == 2

    search_response = api.get("/documents/", params={"q": "sample"})
    assert search_response.status_code == 200
    assert len(search_response.json()) == 2

    owned_response = api.get("/documents/", params={"ownership": "owned"})
    assert owned_response.status_code == 200
    assert all(item["is_owner"] for item in owned_response.json())


def test_document_listing_pagination_and_sorting(api):
    register_and_login(api, "listing_page", "listing_page@example.com")

    assert upload_pdf(api).status_code == 201
    assert upload_pdf(api).status_code == 201

    first_page = api.get(
        "/documents/",
        params={"limit": 1, "offset": 0, "sort_by": "filename", "sort_order": "asc"}
    )
    second_page = api.get(
        "/documents/",
        params={"limit": 1, "offset": 1, "sort_by": "filename", "sort_order": "asc"}
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert len(first_page.json()) == 1
    assert len(second_page.json()) == 1
    assert first_page.json()[0]["id"] != second_page.json()[0]["id"]


def test_document_listing_rejects_invalid_filters(api):
    register_and_login(api, "listing_invalid", "listing_invalid@example.com")

    invalid_ownership = api.get("/documents/", params={"ownership": "everyone"})
    assert invalid_ownership.status_code == 400

    invalid_sort = api.get("/documents/", params={"sort_by": "password"})
    assert invalid_sort.status_code == 400

    invalid_limit = api.get("/documents/", params={"limit": 500})
    assert invalid_limit.status_code == 400

    invalid_date = api.get("/documents/", params={"date_from": "not-a-date"})
    assert invalid_date.status_code == 400

def test_upload_rejects_mime_type_mismatch(api):
    register_and_login(api, "mime_owner", "mime_owner@example.com")

    response = api.post(
        "/documents/upload",
        files={"file": ("fake.pdf", b"%PDF-1.4 fake", "text/plain")}
    )

    assert response.status_code == 400
    assert "File type is not allowed" in response.text


def test_upload_rejects_empty_file(api):
    register_and_login(api, "empty_owner", "empty_owner@example.com")

    response = api.post(
        "/documents/upload",
        files={"file": ("empty.txt", b"", "text/plain")}
    )

    assert response.status_code == 400
    assert "Empty files are not allowed" in response.text


def test_upload_rejects_invalid_docx_archive(api):
    register_and_login(api, "docx_owner", "docx_owner@example.com")

    response = api.post(
        "/documents/upload",
        files={
            "file": (
                "invalid.docx",
                b"PK\x03\x04not-a-valid-zip-archive",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        }
    )

    assert response.status_code == 400
    assert "Invalid Office document archive" in response.text


def test_upload_rejects_invalid_pptx_structure(api):
    register_and_login(api, "pptx_owner", "pptx_owner@example.com")

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as office_file:
        office_file.writestr("[Content_Types].xml", "<Types></Types>")

    response = api.post(
        "/documents/upload",
        files={
            "file": (
                "invalid.pptx",
                archive.getvalue(),
                "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
        }
    )

    assert response.status_code == 400
    assert "Invalid Office document structure" in response.text


def test_upload_rejects_file_over_configured_size_limit(api, monkeypatch):
    register_and_login(api, "size_owner", "size_owner@example.com")
    monkeypatch.setattr(documents_router, "MAX_FILE_SIZE", 10)

    response = api.post(
        "/documents/upload",
        files={
            "file": (
                "large.pdf",
                b"%PDF-1.4 this exceeds the test limit",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 413
    assert "Maximum file size" in response.text

