import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.models.base import Base


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

    yield client

    client.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def register_and_login(client):
    register_response = client.post(
        "/auth/register",
        json={
            "username": "session_user",
            "email": "session@example.com",
            "password": "T3st!SecurePassw0rd"
        }
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": "session@example.com",
            "password": "T3st!SecurePassw0rd"
        }
    )
    assert login_response.status_code == 200
    return login_response


def test_login_sets_session_cookie(api):
    response = register_and_login(api)

    cookie_header = response.headers.get("set-cookie", "")

    assert "securedoc_session=" in cookie_header
    assert "httponly" in cookie_header.lower()
    assert "samesite=lax" in cookie_header.lower()
    assert "max-age=3600" in cookie_header.lower()


def test_authenticated_user_can_access_me(api):
    register_and_login(api)

    response = api.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["username"] == "session_user"


def test_logout_invalidates_current_session(api):
    register_and_login(api)

    logout_response = api.post("/auth/logout")
    assert logout_response.status_code == 200

    response = api.get("/auth/me")

    assert response.status_code == 401
