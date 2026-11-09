import io
import zipfile
from pathlib import Path

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

    assert response.status_code == 200, response.text
    assert response.content.startswith(b"%PDF-")
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.headers["content-disposition"] == "inline"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_pptx_preview_converts_to_pdf(api, tmp_path, monkeypatch):
    register_and_login(api, "pptx_preview_owner", "pptx_preview_owner@example.com")

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as office_file:
        office_file.writestr("[Content_Types].xml", "<Types></Types>")
        office_file.writestr("ppt/presentation.xml", "<presentation></presentation>")

    upload_response = api.post(
        "/documents/upload",
        files={
            "file": (
                "sample.pptx",
                archive.getvalue(),
                "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
        }
    )
    assert upload_response.status_code == 201, upload_response.text
    document_id = upload_response.json()["document_id"]

    fake_soffice = tmp_path / "soffice.com"
    fake_soffice.touch()
    monkeypatch.setattr(documents_router, "SOFFICE_PATH", fake_soffice)

    conversion_directories = []

    def fake_conversion(command, **kwargs):
        output_directory = Path(command[command.index("--outdir") + 1])
        source_file = Path(command[-1])
        output_file = output_directory / f"{source_file.stem}.pdf"
        output_file.write_bytes(b"%PDF-1.4\nMock presentation preview")

        conversion_directories.append(output_directory.parent)

        return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(documents_router.subprocess, "run", fake_conversion)

    response = api.get(f"/documents/{document_id}/preview")

    assert response.status_code == 200, response.text
    assert response.content.startswith(b"%PDF-")
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.headers["content-disposition"] == "inline"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "private, no-store, max-age=0"
    assert conversion_directories
    assert all(not directory.exists() for directory in conversion_directories)


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

    assert response.status_code == 200, response.text
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
    assert replace_response.json()["filename"] == "replacement.pdf"

    list_response = api.get("/documents/")
    assert list_response.status_code == 200
    assert list_response.json()[0]["filename"] == "replacement.pdf"

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

def test_replace_rejects_invalid_pptx_and_preserves_original(api):
    register_and_login(api, "pptx_replace_owner", "pptx_replace_owner@example.com")

    original_archive = io.BytesIO()
    with zipfile.ZipFile(original_archive, "w") as office_file:
        office_file.writestr("[Content_Types].xml", "<Types></Types>")
        office_file.writestr("ppt/presentation.xml", "<presentation></presentation>")

    original_content = original_archive.getvalue()

    upload_response = api.post(
        "/documents/upload",
        files={
            "file": (
                "original.pptx",
                original_content,
                "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
        }
    )
    assert upload_response.status_code == 201, upload_response.text
    document_id = upload_response.json()["document_id"]

    invalid_archive = io.BytesIO()
    with zipfile.ZipFile(invalid_archive, "w") as office_file:
        office_file.writestr("[Content_Types].xml", "<Types></Types>")

    replace_response = api.put(
        f"/documents/{document_id}/replace",
        files={
            "file": (
                "invalid.pptx",
                invalid_archive.getvalue(),
                "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
        }
    )

    assert replace_response.status_code == 400
    assert "Invalid Office document structure" in replace_response.text

    download_response = api.get(f"/documents/{document_id}/download")
    assert download_response.status_code == 200
    assert download_response.content == original_content







def test_viewer_cannot_upload_share_revoke_or_delete(api):
    register_and_login(api, "role_owner", "role_owner@example.com")

    upload_response = upload_pdf(api)
    assert upload_response.status_code == 201, upload_response.text
    document_id = upload_response.json()["document_id"]
    owner_id = api.get("/auth/me").json()["user_id"]

    api.post("/auth/logout")

    viewer_registration = api.post(
        "/auth/register",
        json={
            "username": "role_viewer",
            "email": "role_viewer@example.com",
            "password": "T3st!SecurePassw0rd",
            "role": "viewer"
        }
    )
    assert viewer_registration.status_code == 201, viewer_registration.text

    register_and_login(api, "role_owner", "role_owner@example.com")
    viewer_id = None

    api.post("/auth/logout")
    response = api.post(
        "/auth/login",
        json={
            "email": "role_viewer@example.com",
            "password": "T3st!SecurePassw0rd"
        }
    )
    assert response.status_code == 200, response.text
    viewer_id = api.get("/auth/me").json()["user_id"]

    api.post("/auth/logout")
    register_and_login(api, "role_owner", "role_owner@example.com")

    grant_response = api.post(
        f"/documents/{document_id}/permissions",
        json={"user_id": viewer_id, "access_level": "viewer"}
    )
    assert grant_response.status_code == 200, grant_response.text

    api.post("/auth/logout")
    response = api.post(
        "/auth/login",
        json={
            "email": "role_viewer@example.com",
            "password": "T3st!SecurePassw0rd"
        }
    )
    assert response.status_code == 200, response.text

    upload_denied = upload_pdf(api)
    assert upload_denied.status_code == 403

    grant_denied = api.post(
        f"/documents/{document_id}/permissions",
        json={"user_id": owner_id, "access_level": "editor"}
    )
    assert grant_denied.status_code == 403

    revoke_denied = api.delete(
        f"/documents/{document_id}/permissions/{viewer_id}"
    )
    assert revoke_denied.status_code == 403

    delete_denied = api.delete(f"/documents/{document_id}")
    assert delete_denied.status_code == 403

    download_allowed = api.get(
        f"/documents/{document_id}/download"
    )
    assert download_allowed.status_code == 200


def test_document_category_upload_and_filter(api):
    register_and_login(api, "category_owner", "category_owner@example.com")

    hr_upload = api.post(
        "/documents/upload",
        data={"category": "HR"},
        files={"file": ("hr-policy.pdf", b"%PDF-1.4\nHR policy", "application/pdf")}
    )
    assert hr_upload.status_code == 201, hr_upload.text
    assert hr_upload.json()["category"] == "HR"

    finance_upload = api.post(
        "/documents/upload",
        data={"category": "Finance"},
        files={"file": ("finance-report.pdf", b"%PDF-1.4\nFinance report", "application/pdf")}
    )
    assert finance_upload.status_code == 201, finance_upload.text
    assert finance_upload.json()["category"] == "Finance"

    all_documents = api.get("/documents/")
    assert all_documents.status_code == 200, all_documents.text
    assert len(all_documents.json()) == 2

    hr_documents = api.get("/documents/", params={"category": "HR"})
    assert hr_documents.status_code == 200, hr_documents.text
    assert len(hr_documents.json()) == 1
    assert hr_documents.json()[0]["category"] == "HR"
    assert hr_documents.json()[0]["filename"] == "hr-policy.pdf"


def test_uploaded_document_is_not_publicly_accessible(api):
    register_and_login(api, "private_storage_owner", "private_storage_owner@example.com")

    upload_response = upload_pdf(api)
    assert upload_response.status_code == 201, upload_response.text
    document_id = upload_response.json()["document_id"]

    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)

    try:
        stored_document = db.get(document.Document, document_id)
        assert stored_document is not None
        stored_filename = stored_document.stored_filename
    finally:
        db_generator.close()

    stored_file = documents_router.STORAGE_DIR / stored_filename
    assert stored_file.is_file()

    storage_url_response = api.get(
        f"/storage/uploads/{stored_filename}"
    )
    assert storage_url_response.status_code == 404

    uploads_url_response = api.get(
        f"/uploads/{stored_filename}"
    )
    assert uploads_url_response.status_code == 404

def test_edit_preserves_committed_file_when_backup_cleanup_fails(api, monkeypatch):
    register_and_login(api, "cleanup_edit_owner", "cleanup_edit_owner@example.com")

    upload_response = api.post(
        "/documents/upload",
        files={"file": ("cleanup.txt", b"Original content", "text/plain")}
    )
    assert upload_response.status_code == 201, upload_response.text
    document_id = upload_response.json()["document_id"]
    stored_file = next(documents_router.STORAGE_DIR.iterdir())

    original_unlink = Path.unlink
    backup_paths = []

    def fail_backup_cleanup(path, *args, **kwargs):
        if path.suffix == ".bak":
            backup_paths.append(path)
            raise PermissionError("Simulated backup lock")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_backup_cleanup)

    updated_content = "Updated content after commit"
    response = api.put(
        f"/documents/{document_id}/edit",
        json={"content": updated_content}
    )

    assert response.status_code == 200, response.text
    assert response.json()["file_size"] == len(updated_content.encode("utf-8"))
    assert stored_file.read_bytes() == updated_content.encode("utf-8")
    assert len(backup_paths) == 1
    assert backup_paths[0].is_file()
    assert backup_paths[0].read_bytes() == b"Original content"


def test_replace_preserves_committed_file_when_backup_cleanup_fails(api, monkeypatch):
    register_and_login(api, "cleanup_replace_owner", "cleanup_replace_owner@example.com")

    upload_response = upload_pdf(api)
    assert upload_response.status_code == 201, upload_response.text
    document_id = upload_response.json()["document_id"]
    stored_file = next(documents_router.STORAGE_DIR.iterdir())
    original_content = stored_file.read_bytes()

    original_unlink = Path.unlink
    backup_paths = []

    def fail_backup_cleanup(path, *args, **kwargs):
        if path.suffix == ".bak":
            backup_paths.append(path)
            raise PermissionError("Simulated backup lock")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_backup_cleanup)

    replacement_content = b"%PDF-1.7\nReplacement after commit"
    response = api.put(
        f"/documents/{document_id}/replace",
        files={
            "file": ("cleanup-replacement.pdf", replacement_content, "application/pdf")
        }
    )

    assert response.status_code == 200, response.text
    assert response.json()["filename"] == "cleanup-replacement.pdf"
    assert response.json()["file_size"] == len(replacement_content)
    assert stored_file.read_bytes() == replacement_content
    assert len(backup_paths) == 1
    assert backup_paths[0].is_file()
    assert backup_paths[0].read_bytes() == original_content

