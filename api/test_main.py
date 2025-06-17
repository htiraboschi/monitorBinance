from fastapi.testclient import TestClient
from fastapi import status
from api.main import app

client = TestClient(app)


def test_get_reglas_from_db():
    response = client.get("/reglas")
    assert response.status_code == status.HTTP_200_OK