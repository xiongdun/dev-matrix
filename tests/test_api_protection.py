"""API 权限保护测试。

测试受保护路由是否需要认证，以及公开路由是否可免认证访问。
"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.main import app
from app.state.models import Base, SystemSecretModel, UserModel, get_db


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
    if (
        not db.query(SystemSecretModel)
        .filter(SystemSecretModel.key_name == "jwt_secret_key")
        .first()
    ):
        db.add(
            SystemSecretModel(
                key_name="jwt_secret_key", key_value="test-secret-key-for-testing-only"
            )
        )
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


@pytest.fixture
def auth_token(client, test_user):
    """获取测试用户的认证 Token。"""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "testpass123",
        },
    )
    assert response.status_code == 200
    return response.json()["token"]


@pytest.fixture
def auth_headers(auth_token):
    """认证请求头。"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestApiProtection:
    """API 路由保护测试。"""

    def test_protected_route_without_token(self, client):
        """测试未认证访问受保护路由。"""
        protected_routes = [
            ("GET", "/api/users"),
            ("GET", "/api/roles"),
        ]

        for method, path in protected_routes:
            response = client.request(method, path)
            assert response.status_code == 401, f"{method} {path} should require auth"

    def test_protected_route_with_valid_token(self, client, auth_headers):
        """测试认证后访问受保护路由。"""
        response = client.get("/api/users", headers=auth_headers)
        assert response.status_code != 401

    def test_public_route_without_token(self, client):
        """测试公开路由无需认证。"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_login_route_public(self, client):
        """测试登录路由是公开的。"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "any",
                "password": "any",
            },
        )
        assert response.status_code in (401, 200)
