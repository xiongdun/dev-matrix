"""CORS 配置测试。"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.main import app
from app.state.models import Base, UserModel, get_db


@pytest.fixture
def db_session():
    """创建共享文件数据库会话。"""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_url = f"sqlite:///{db_path}"

    from app.config import get_settings

    original_db_url = get_settings().database_url
    get_settings().database_url = db_url

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()
        get_settings().database_url = original_db_url
        from app.state.models import _engine, _SessionLocal

        global _engine, _SessionLocal
        if _engine is not None:
            _engine.dispose()
            _engine = None
        if _SessionLocal is not None:
            _SessionLocal = None
        try:
            os.unlink(db_path)
        except OSError:
            pass


@pytest.fixture
def client(db_session):
    """创建测试客户端。"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # 重置限流器状态
    from app.core.limiter import limiter

    limiter.reset()

    user = UserModel(
        username="testuser",
        password_hash=hash_password("testpass"),
        status="active",
    )
    db_session.add(user)
    db_session.commit()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestCors:
    def test_allowed_origin(self, client):
        """允许的来源可以访问。"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_headers_present(self, client):
        """CORS 响应头存在。"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.status_code == 200
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-credentials" in response.headers

    def test_preflight_allowed_methods(self, client):
        """预检请求验证允许的方法包含 POST。"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert response.status_code == 200
        allowed_methods = response.headers.get("access-control-allow-methods", "")
        assert "POST" in allowed_methods

    def test_preflight_contains_get(self, client):
        """预检请求验证允许的方法包含 GET。"""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        allowed_methods = response.headers.get("access-control-allow-methods", "")
        assert "GET" in allowed_methods
