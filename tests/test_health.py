"""健康检查 API 测试。"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealth:
    """测试健康检查端点。"""

    def test_health_live(self):
        """测试 /health/live 存活探针。"""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["checks"]["app"] == "running"

    def test_health_ready(self):
        """测试 /health/ready 就绪探针。"""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "temporal" in data["checks"]
        assert "redis" in data["checks"]

    def test_health(self):
        """测试 /health 综合健康检查。"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "version" in data
