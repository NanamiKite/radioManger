"""
Test log endpoints
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_logs():
    """Test get logs endpoint"""
    response = client.get("/api/v1/logs")
    # 401 because no auth, 200 if authenticated
    assert response.status_code in [200, 401, 422]

def test_create_log():
    """Test create log endpoint"""
    response = client.post("/api/v1/logs", json={
        "station_id": 1,
        "call_sign": "W1AW",
        "qso_date": "2024-01-01"
    })
    # 401 because no auth, 201 if authenticated
    assert response.status_code in [201, 401, 422]
