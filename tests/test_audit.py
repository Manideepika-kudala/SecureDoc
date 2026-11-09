import pytest

from sqlalchemy import create_engine, select, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import _configure_sqlite_audit_protection
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

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        _configure_sqlite_audit_protection(connection)

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



def test_audit_log_cannot_be_updated(db):
    event = record_audit_event(
        db=db,
        action="document_access",
        outcome="denied",
        details={"reason": "unauthorized"},
    )
    db.commit()

    event.outcome = "success"

    with pytest.raises(IntegrityError, match="Audit logs are append-only"):
        db.commit()

    db.rollback()


def test_audit_log_cannot_be_deleted(db):
    event = record_audit_event(
        db=db,
        action="document_access",
        outcome="denied",
        details={"reason": "unauthorized"},
    )
    db.commit()

    db.delete(event)

    with pytest.raises(IntegrityError, match="Audit logs are append-only"):
        db.commit()

    db.rollback()



def test_audit_log_survives_actor_user_deletion(db):
    user = User(
        username="deletedactor",
        email="deletedactor@example.com",
        password_hash="test-hash",
    )
    db.add(user)
    db.flush()

    event = record_audit_event(
        db=db,
        action="document_access",
        outcome="success",
        actor_user_id=user.id,
        details={"test": "actor deletion"},
    )
    db.commit()

    event_id = event.id
    db.delete(user)
    db.commit()

    saved = db.get(AuditLog, event_id)
    assert saved is not None
    assert saved.actor_user_id is None
    assert saved.details["test"] == "actor deletion"


def test_audit_log_survives_document_deletion(db):
    user = User(
        username="documentowner",
        email="documentowner@example.com",
        password_hash="test-hash",
    )
    db.add(user)
    db.flush()

    document = Document(
        owner_id=user.id,
        original_filename="audit-test.pdf",
        stored_filename="audit-test.pdf",
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
        details={"test": "document deletion"},
    )
    db.commit()

    event_id = event.id
    db.delete(document)
    db.commit()

    saved = db.get(AuditLog, event_id)
    assert saved is not None
    assert saved.document_id is None
    assert saved.actor_user_id == user.id
    assert saved.details["test"] == "document deletion"



def test_audit_log_cannot_be_updated_with_direct_sql(db):
    event = record_audit_event(
        db=db,
        action="document_access",
        outcome="denied",
        details={"reason": "unauthorized"},
    )
    db.commit()

    with pytest.raises(IntegrityError, match="Audit logs are append-only"):
        db.execute(
            text("""
                UPDATE audit_logs
                SET outcome = 'success'
                WHERE id = :event_id
            """),
            {"event_id": event.id},
        )


def test_audit_log_cannot_be_deleted_with_direct_sql(db):
    event = record_audit_event(
        db=db,
        action="document_access",
        outcome="denied",
        details={"reason": "unauthorized"},
    )
    db.commit()

    with pytest.raises(IntegrityError, match="Audit logs are append-only"):
        db.execute(
            text("DELETE FROM audit_logs WHERE id = :event_id"),
            {"event_id": event.id},
        )



@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"action": ""}, "non-empty string"),
        ({"action": " "}, "non-empty string"),
        ({"outcome": []}, "Invalid audit outcome"),
        ({"action": "a" * 51}, "50 characters"),
        ({"details": ["invalid"]}, "dictionary"),
        ({"ip_address": 123}, "must be a string"),
        ({"ip_address": "a" * 46}, "45 characters"),
    ],
)
def test_invalid_audit_fields_are_rejected(db, kwargs, message):
    arguments = {
        "action": "document_access",
        "outcome": "success",
    }
    arguments.update(kwargs)

    with pytest.raises(ValueError, match=message):
        record_audit_event(db=db, **arguments)


def test_audit_event_accepts_maximum_action_and_ip_lengths(db):
    event = record_audit_event(
        db=db,
        action="a" * 50,
        outcome="success",
        ip_address="1" * 45,
    )

    assert len(event.action) == 50
    assert len(event.ip_address) == 45
