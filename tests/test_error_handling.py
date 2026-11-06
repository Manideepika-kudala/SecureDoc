import logging

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.main import (
    http_exception_handler,
    validation_exception_handler,
    unexpected_exception_handler,
)


error_app = FastAPI()

error_app.add_exception_handler(
    StarletteHTTPException,
    http_exception_handler
)
error_app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler
)
error_app.add_exception_handler(
    Exception,
    unexpected_exception_handler
)


@error_app.get("/not-found")
def not_found():
    raise HTTPException(status_code=404, detail="Document not found")


@error_app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}


@error_app.get("/unexpected")
def unexpected():
    raise RuntimeError("Sensitive internal database detail")


def test_http_error_returns_correct_status_and_message():
    client = TestClient(error_app)

    response = client.get("/not-found")

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"


def test_validation_error_returns_structured_response():
    client = TestClient(error_app)

    response = client.get("/items/invalid")

    assert response.status_code == 422
    data = response.json()

    assert data["detail"] == "Request validation failed"
    assert len(data["errors"]) > 0
    assert "field" in data["errors"][0]
    assert "message" in data["errors"][0]


def test_unexpected_error_hides_internal_details_and_logs(caplog):
    client = TestClient(error_app, raise_server_exceptions=False)

    with caplog.at_level(logging.ERROR, logger="securedoc"):
        response = client.get("/unexpected")

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "An unexpected error occurred. Please try again later."
    )
    assert "Sensitive internal database detail" not in response.text
    assert "Sensitive internal database detail" in caplog.text


