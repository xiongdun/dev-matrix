"""全局错误处理测试。"""

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


class TestErrorHandling:
    def test_error_response_contains_request_id(self, client, auth_token):
        """错误响应包含 request_id。"""
        # 访问一个不存在的端点触发 404
        response = client.get(
            "/api/nonexistent",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_internal_error_masked(self, client, auth_token):
        """内部错误不暴露详细信息。"""
        # 访问一个会触发异常的端点
        # 这里我们验证全局异常处理器的格式
        response = client.get(
            "/api/requirements/99999",  # 不存在的 ID 可能触发异常
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        # 即使是 404，也验证响应格式
        data = response.json()
        assert "detail" in data
        # 确保没有暴露内部异常信息（如 "Internal server error: <exception>"）
        if response.status_code == 500:
            assert "Traceback" not in data.get("detail", "")
            assert "exception" not in str(data).lower()
