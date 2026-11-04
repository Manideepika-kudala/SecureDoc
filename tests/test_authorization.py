import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.user import User
from app.models.document import Document
from app.models.permission import DocumentPermission
from app.services.authorization import get_authorized_document


@pytest.fixture
def db(tmp_path):
    database_path = tmp_path / "test_securedoc.db"
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False}
    )

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)

    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def sample_data(db):
    owner = User(
        username="owner",
        email="owner@example.com",
        password_hash="test_hash",
        is_active=True
    )
    viewer = User(
        username="viewer",
        email="viewer@example.com",
        password_hash="test_hash",
        is_active=True
    )
    editor = User(
        username="editor",
        email="editor@example.com",
        password_hash="test_hash",
        is_active=True
    )

    db.add_all([owner, viewer, editor])
    db.commit()

    document = Document(
        owner_id=owner.id,
        original_filename="sample.pdf",
        stored_filename="sample_test.pdf",
        content_type="application/pdf",
        file_size=100
    )
    db.add(document)
    db.commit()

    viewer_permission = DocumentPermission(
        document_id=document.id,
        user_id=viewer.id,
        granted_by=owner.id,
        access_level="viewer"
    )
    editor_permission = DocumentPermission(
        document_id=document.id,
        user_id=editor.id,
        granted_by=owner.id,
        access_level="editor"
    )

    db.add_all([viewer_permission, editor_permission])
    db.commit()

    return {
        "owner": owner,
        "viewer": viewer,
        "editor": editor,
        "document": document,
        "viewer_permission": viewer_permission
    }


def test_owner_can_access_document(db, sample_data):
    document = get_authorized_document(
        sample_data["document"].id,
        sample_data["owner"],
        db
    )
    assert document.id == sample_data["document"].id


def test_viewer_can_view_document(db, sample_data):
    document = get_authorized_document(
        sample_data["document"].id,
        sample_data["viewer"],
        db,
        required_level="viewer"
    )
    assert document.id == sample_data["document"].id


def test_editor_can_access_document(db, sample_data):
    document = get_authorized_document(
        sample_data["document"].id,
        sample_data["editor"],
        db,
        required_level="editor"
    )
    assert document.id == sample_data["document"].id


def test_viewer_cannot_edit_document(db, sample_data):
    with pytest.raises(HTTPException) as error:
        get_authorized_document(
            sample_data["document"].id,
            sample_data["viewer"],
            db,
            required_level="editor"
        )

    assert error.value.status_code == 403


def test_revoked_permission_is_denied_immediately(db, sample_data):
    db.delete(sample_data["viewer_permission"])
    db.commit()

    with pytest.raises(HTTPException) as error:
        get_authorized_document(
            sample_data["document"].id,
            sample_data["viewer"],
            db
        )

    assert error.value.status_code == 403


def test_unshared_user_cannot_access_document(db, sample_data):
    unauthorized_user = User(
        username="outsider",
        email="outsider@example.com",
        password_hash="test_hash",
        is_active=True
    )
    db.add(unauthorized_user)
    db.commit()

    with pytest.raises(HTTPException) as error:
        get_authorized_document(
            sample_data["document"].id,
            unauthorized_user,
            db
        )

    assert error.value.status_code == 403
