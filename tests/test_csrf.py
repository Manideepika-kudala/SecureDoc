from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.csrf import CSRFMiddleware


app = FastAPI()
app.add_middleware(CSRFMiddleware, secure=False)


@app.get("/")
def home():
    return {"status": "ok"}


@app.post("/mutate")
def mutate():
    return {"changed": True}


def test_safe_request_sets_csrf_cookie():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert client.cookies.get("csrf_token")


def test_unsafe_request_without_token_is_rejected():
    client = TestClient(app)

    response = client.post("/mutate")

    assert response.status_code == 403


def test_unsafe_request_with_invalid_token_is_rejected():
    client = TestClient(app)
    client.get("/")

    response = client.post(
        "/mutate",
        headers={"X-CSRF-Token": "invalid-token"}
    )

    assert response.status_code == 403


def test_unsafe_request_with_matching_token_is_allowed():
    client = TestClient(app)
    client.get("/")

    token = client.cookies.get("csrf_token")

    response = client.post(
        "/mutate",
        headers={"X-CSRF-Token": token}
    )

    assert response.status_code == 200
    assert response.json() == {"changed": True}
