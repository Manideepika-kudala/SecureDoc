import pytest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.user import User
from app.models.document import Document
from app.models.permission import DocumentPermission
from app.models.audit import AuditLog
from app.services.audit import record_audit_event


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)

    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_successful_audit_event_is_saved(db):
    user = User(
        username="audituser",
        email="audit@example.com",
        password_hash="test-hash",
    )
    db.add(user)
    db.flush()

    document = Document(
        owner_id=user.id,
        original_filename="report.pdf",
        stored_filename="test-report.pdf",
        content_type="application/pdf",
        file_size=100,
    )
    db.add(document)
    db.flush()

    event = record_audit_event(
        db=db,
        action="document_upload",
        outcome="success",
        actor_user_id=user.id,
        document_id=document.id,
        details={"filename": "report.pdf"},
        ip_address="127.0.0.1",
    )

    db.commit()

    saved = db.scalar(
        select(AuditLog).where(AuditLog.id == event.id)
    )

    assert saved is not None
    assert saved.action == "document_upload"
    assert saved.outcome == "success"
    assert saved.actor_user_id == user.id
    assert saved.document_id == document.id


def test_denied_audit_event_is_saved(db):
    event = record_audit_event(
        db=db,
        action="document_access",
        outcome="denied",
        actor_user_id=None,
        document_id=None,
        details={"reason": "unauthorized"},
        ip_address="127.0.0.1",
    )

    db.commit()

    saved = db.scalar(
        select(AuditLog).where(AuditLog.id == event.id)
    )

    assert saved is not None
    assert saved.outcome == "denied"
    assert saved.details["reason"] == "unauthorized"


def test_invalid_outcome_is_rejected(db):
    with pytest.raises(ValueError):
        record_audit_event(
            db=db,
            action="document_access",
            outcome="unknown",
        )
