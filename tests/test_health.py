from fastapi.testclient import TestClient

from app.main import create_app


def test_imports_and_health() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "kanban-prompt-companion"}
