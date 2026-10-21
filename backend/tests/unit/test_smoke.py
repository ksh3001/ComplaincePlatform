from fastapi.testclient import TestClient

from app.main import app


def test_ping() -> None:
    assert TestClient(app).get("/api/v1/ping").json() == {"status": "ok"}
