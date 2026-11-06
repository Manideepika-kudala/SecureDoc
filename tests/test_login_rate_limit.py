import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.models.base import Base
from app.models.login_attempt import LoginAttempt


@pytest.fixture
def api():
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

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    client.get('/')
    csrf_token = client.cookies.get('csrf_token')
    client.headers.update({'X-CSRF-Token': csrf_token})

    yield client, TestingSession

    client.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "username": "rate_user",
            "email": "rate@example.com",
            "password": "T3st!SecurePassw0rd"
        }
    )
    assert response.status_code == 201, response.text


def test_five_failed_attempts_block_sixth_login(api):
    client, _ = api
    register_user(client)

    for _ in range(5):
        response = client.post(
            "/auth/login",
            json={
                "email": "rate@example.com",
                "password": "WrongPassword123!"
            }
        )
        assert response.status_code == 401

    response = client.post(
        "/auth/login",
        json={
            "email": "rate@example.com",
            "password": "WrongPassword123!"
        }
    )

    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_successful_login_resets_failed_attempts(api):
    client, TestingSession = api
    register_user(client)

    for _ in range(2):
        response = client.post(
            "/auth/login",
            json={
                "email": "rate@example.com",
                "password": "WrongPassword123!"
            }
        )
        assert response.status_code == 401

    response = client.post(
        "/auth/login",
        json={
            "email": "rate@example.com",
            "password": "T3st!SecurePassw0rd"
        }
    )

    assert response.status_code == 200

    db = TestingSession()
    try:
        attempt = db.scalar(
            select(LoginAttempt).where(
                LoginAttempt.ip_address == "testclient"
            )
        )
        assert attempt is None
    finally:
        db.close()
