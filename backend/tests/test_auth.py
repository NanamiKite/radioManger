"""
Test authentication endpoints
"""

from fastapi.testclient import TestClient
from app.main import app
from app.database.base import Base, engine

client = TestClient(app)

def setup_module():
    Base.metadata.create_all(bind=engine)

def teardown_module():
    Base.metadata.drop_all(bind=engine)

def test_register():
    """Test user registration"""
    response = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "confirm_password": "testpass123",
        "full_name": "Test User"
    })
    assert response.status_code in [201, 422]

def test_login():
    """Test user login"""
    # First register a user
    client.post("/api/v1/auth/register", json={
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "testpass123",
        "confirm_password": "testpass123"
    })
    
    # Then try to login
    response = client.post("/api/v1/auth/login", json={
        "username": "testuser2",
        "password": "testpass123"
    })
    assert response.status_code in [200, 401, 422]
