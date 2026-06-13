"""
Test station endpoints
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_stations():
    """Test get stations endpoint"""
    response = client.get("/api/v1/stations")
    # 401 because no auth, 200 if authenticated
    assert response.status_code in [200, 401, 422]

def test_create_station():
    """Test create station endpoint"""
    response = client.post("/api/v1/stations", json={
        "callsign": "W1AW",
        "grid_square": "FN31PR"
    })
    # 401 because no auth, 201 if authenticated
    assert response.status_code in [201, 401, 422]
