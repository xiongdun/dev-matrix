"""认证 API 测试。

测试登录、Token 刷新、获取当前用户等认证相关功能。
"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.state.models import Base, UserModel, get_db, SystemSecretModel
from app.core.security import hash_password
from app.main import app


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

    # 初始化 JWT secret
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    if not db.query(SystemSecretModel).filter(SystemSecretModel.key_name == "jwt_secret_key").first():
        db.add(SystemSecretModel(key_name="jwt_secret_key", key_value="test-secret-key-for-testing-only"))
        db.commit()
    db.close()

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

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """创建测试用户。"""
    existing = db_session.query(UserModel).filter(UserModel.username == "testuser").first()
    if existing:
        db_session.delete(existing)
        db_session.commit()
    user = UserModel(
        username="testuser",
        password_hash=hash_password("testpass123"),
        nickname="Test User",
        email="test@example.com",
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    yield user


class TestLogin:
    """登录接口测试。"""

    def test_login_success(self, client, test_user):
        """测试正常登录。"""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "refresh_token" in data
        assert data["user"]["username"] == "testuser"

    def test_login_wrong_password(self, client, test_user):
        """测试密码错误。"""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """测试不存在的用户。"""
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "anypassword",
        })
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        """测试缺少必填字段。"""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
        })
        assert response.status_code == 422


class TestTokenRefresh:
    """Token 刷新测试。"""

    def test_refresh_token_success(self, client, test_user):
        """测试正常刷新 Token。"""
        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123",
        })
        refresh_token = login_response.json()["refresh_token"]

        response = client.post("/api/auth/refresh", headers={
            "Authorization": f"Bearer {refresh_token}",
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data

    def test_refresh_token_invalid(self, client):
        """测试无效的 refresh token。"""
        response = client.post("/api/auth/refresh", headers={
            "Authorization": "Bearer invalid_token",
        })
        assert response.status_code == 401


class TestGetMe:
    """获取当前用户信息测试。"""

    def test_get_me_success(self, client, test_user):
        """测试获取当前用户信息。"""
        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass123",
        })
        token = login_response.json()["token"]

        response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

    def test_get_me_no_token(self, client):
        """测试未提供 Token。"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """测试无效的 Token。"""
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid_token",
        })
        assert response.status_code == 401
