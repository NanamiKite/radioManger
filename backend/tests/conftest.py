"""
RadioManager API - 测试套件

运行所有测试: pytest
运行特定测试: pytest tests/test_auth.py
带覆盖率报告: pytest --cov=app
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.base import Base, engine

# 创建测试客户端
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown():
    """为每个测试创建和清理数据库表"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_root():
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "RadioManager API"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
