import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.models.base import Base
from app.models.audit import AuditLog


@pytest.fixture
def api():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSession = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    client.get("/")
    csrf_token = client.cookies.get("csrf_token")
    client.headers.update({"X-CSRF-Token": csrf_token})

    yield client, TestingSession

    client.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def register_user(client):
    return client.post(
        "/auth/register",
        json={
            "username": "audit_user",
            "email": "audit@example.com",
            "password": "T3st!SecurePassw0rd",
        },
    )


def get_audit_events(TestingSession, action):
    db = TestingSession()
    try:
        return db.scalars(
            select(AuditLog)
            .where(AuditLog.action == action)
            .order_by(AuditLog.id)
        ).all()
    finally:
        db.close()


def test_successful_registration_is_audited(api):
    client, TestingSession = api

    response = register_user(client)

    assert response.status_code == 201, response.text

    events = get_audit_events(TestingSession, "auth_register")

    assert len(events) == 1
    assert events[0].outcome == "success"
    assert events[0].actor_user_id is not None


def test_duplicate_registration_is_audited_as_denied(api):
    client, TestingSession = api

    first_response = register_user(client)
    assert first_response.status_code == 201

    second_response = register_user(client)
    assert second_response.status_code == 409

    events = get_audit_events(TestingSession, "auth_register")

    assert len(events) == 2
    assert events[1].outcome == "denied"
    assert events[1].details["reason"] == (
        "username_or_email_already_registered"
    )


def test_failed_login_is_audited(api):
    client, TestingSession = api

    register_response = register_user(client)
    assert register_response.status_code == 201

    response = client.post(
        "/auth/login",
        json={
            "email": "audit@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401

    events = get_audit_events(TestingSession, "auth_login")

    assert len(events) == 1
    assert events[0].outcome == "denied"
    assert events[0].details["reason"] == "invalid_credentials"


def test_successful_login_and_logout_are_audited(api):
    client, TestingSession = api

    register_response = register_user(client)
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": "audit@example.com",
            "password": "T3st!SecurePassw0rd",
        },
    )

    assert login_response.status_code == 200

    logout_response = client.post("/auth/logout")

    assert logout_response.status_code == 200

    login_events = get_audit_events(TestingSession, "auth_login")
    logout_events = get_audit_events(TestingSession, "auth_logout")

    assert len(login_events) == 1
    assert login_events[0].outcome == "success"

    assert len(logout_events) == 1
    assert logout_events[0].outcome == "success"
    assert logout_events[0].actor_user_id == (
        login_events[0].actor_user_id
    )
