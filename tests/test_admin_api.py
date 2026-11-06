import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db
from app.models.base import Base
from app.models.user import User
from app.models.audit import AuditLog


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


def register_and_login(client, username, email):
    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "T3st!SecurePassw0rd"
        }
    )
    assert response.status_code == 201, response.text

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "T3st!SecurePassw0rd"
        }
    )
    assert response.status_code == 200, response.text


def test_admin_can_view_activity(api):
    client, TestingSession = api

    register_and_login(
        client, "admin_user", "admin@example.com"
    )

    with TestingSession() as db:
        user = db.query(User).filter_by(
            username="admin_user"
        ).one()
        user.is_admin = True
        db.commit()

        db.add(
            AuditLog(
                actor_user_id=user.id,
                action="login",
                outcome="success",
                details={"source": "test"}
            )
        )
        db.commit()

    response = client.get("/admin/activity")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["action"] == "login"


def test_normal_user_cannot_view_activity(api):
    client, TestingSession = api

    register_and_login(
        client, "normal_user", "normal@example.com"
    )

    response = client.get("/admin/activity")

    assert response.status_code == 403


def test_unauthenticated_user_cannot_view_activity(api):
    client, TestingSession = api

    response = client.get("/admin/activity")

    assert response.status_code == 401


def test_admin_activity_filters_and_pagination(api):
    client, TestingSession = api

    register_and_login(
        client, "filter_admin", "filteradmin@example.com"
    )

    with TestingSession() as db:
        user = db.query(User).filter_by(
            username="filter_admin"
        ).one()
        user.is_admin = True

        db.add_all([
            AuditLog(
                actor_user_id=user.id,
                action="login",
                outcome="success",
                details={}
            ),
            AuditLog(
                actor_user_id=user.id,
                action="document_access",
                outcome="denied",
                details={}
            ),
            AuditLog(
                actor_user_id=user.id,
                action="login",
                outcome="success",
                details={}
            ),
        ])
        db.commit()

    response = client.get(
        "/admin/activity",
        params={
            "outcome": "success",
            "action": "login",
            "limit": 1,
            "offset": 0
        }
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total"] == 2
    assert data["limit"] == 1
    assert data["offset"] == 0
    assert len(data["items"]) == 1
    assert data["items"][0]["outcome"] == "success"


def test_admin_can_view_overview(api):
    client, TestingSession = api

    register_and_login(
        client, "overview_admin", "overviewadmin@example.com"
    )

    with TestingSession() as db:
        user = db.query(User).filter_by(
            username="overview_admin"
        ).one()
        user.is_admin = True
        db.commit()

        db.add(
            AuditLog(
                actor_user_id=user.id,
                action="login",
                outcome="success",
                details={}
            )
        )
        db.commit()

    response = client.get("/admin/overview")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total_users"] == 1
    assert data["total_documents"] == 0
    assert data["total_events"] == 1
    assert data["successful_events"] == 1
    assert data["denied_events"] == 0


def test_normal_user_cannot_view_overview(api):
    client, TestingSession = api

    register_and_login(
        client, "overview_user", "overviewuser@example.com"
    )

    response = client.get("/admin/overview")

    assert response.status_code == 403


def test_unauthenticated_user_cannot_view_overview(api):
    client, TestingSession = api

    response = client.get("/admin/overview")

    assert response.status_code == 401



def test_admin_activity_rejects_sql_injection_payload(api):
    client, TestingSession = api

    register_and_login(
        client, "sqli_admin", "sqli_admin@example.com"
    )

    with TestingSession() as db:
        admin_user = db.query(User).filter_by(
            username="sqli_admin"
        ).one()
        admin_user.is_admin = True

        db.add_all([
            AuditLog(
                actor_user_id=admin_user.id,
                action="login",
                outcome="success",
                details={}
            ),
            AuditLog(
                actor_user_id=admin_user.id,
                action="document_access",
                outcome="denied",
                details={}
            ),
        ])
        db.commit()

    response = client.get(
        "/admin/activity",
        params={"action": "' OR 1=1 --"}
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []
