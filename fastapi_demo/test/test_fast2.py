from fastapi.testclient import TestClient
from fastapi import status
from ..fast2 import app2

client = TestClient(app2)


def test_return_health_check():
    response = client.get("/healthy")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'status': 'Healthy'}
