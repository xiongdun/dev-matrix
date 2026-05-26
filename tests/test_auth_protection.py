"""API 认证保护测试。"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.state.models import Base, UserModel, get_db
from app.core.security import hash_password
from app.main import app


@pytest.fixture
def db_session():
    """创建共享文件数据库会话，确保 lifespan 和测试使用同一数据库。"""
    # 使用临时文件数据库，使 lifespan 和测试共享同一数据库
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_url = f"sqlite:///{db_path}"

    # 临时修改配置中的数据库 URL
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
        # 恢复原始配置
        get_settings().database_url = original_db_url
        # 清理全局引擎缓存，避免影响其他测试
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

    # 创建测试用户
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


@pytest.fixture
def auth_token(client, db_session):
    """获取认证 Token。"""
    response = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "testpass",
    })
    assert response.status_code == 200
    return response.json()["token"]


class TestProtectedRoutes:
    def test_requirements_without_auth(self, client):
        """未认证访问 /api/requirements 返回 401。"""
        response = client.get("/api/requirements/")
        assert response.status_code == 401

    def test_requirements_with_auth(self, client, auth_token):
        """认证后访问 /api/requirements 返回 200。"""
        response = client.get(
            "/api/requirements/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200

    def test_projects_without_auth(self, client):
        """未认证访问 /api/projects 返回 401。"""
        response = client.get("/api/projects/")
        assert response.status_code == 401

    def test_projects_with_auth(self, client, auth_token):
        """认证后访问 /api/projects 返回 200。"""
        response = client.get(
            "/api/projects/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200

    def test_workflow_without_auth(self, client):
        """未认证访问 /api/workflow/{project_id}/status 返回 401。"""
        response = client.get("/api/workflow/test-project/status")
        assert response.status_code == 401

    def test_users_without_auth(self, client):
        """未认证访问 /api/users 返回 401。"""
        response = client.get("/api/users/")
        assert response.status_code == 401

    def test_roles_without_auth(self, client):
        """未认证访问 /api/roles 返回 401。"""
        response = client.get("/api/roles/")
        assert response.status_code == 401


class TestPublicRoutes:
    def test_auth_login_public(self, client):
        """登录接口无需认证。"""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass",
        })
        assert response.status_code == 200

    def test_health_public(self, client):
        """健康检查接口无需认证。"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_menus_public(self, client):
        """菜单接口在 main.py 层面无需认证，但内部有认证依赖。"""
        response = client.get("/api/menus/")
        # menus.py 内部路由有 get_current_user 依赖，所以返回 401
        # main.py 将 menus 列为公开路由，但内部逻辑仍需要认证
        assert response.status_code == 401


class TestInvalidToken:
    def test_invalid_token(self, client):
        """无效 Token 返回 401。"""
        response = client.get(
            "/api/requirements/",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_missing_token(self, client):
        """缺少 Token 返回 401。"""
        response = client.get("/api/requirements/")
        assert response.status_code == 401

    def test_wrong_prefix(self, client):
        """错误的 Authorization 前缀返回 401。"""
        response = client.get(
            "/api/requirements/",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        assert response.status_code == 401
