"""API 限流测试。"""

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


class TestRateLimit:
    def test_login_rate_limit(self, client):
        """登录接口 5 次/分钟限流生效。"""
        # 先成功登录 5 次
        for i in range(5):
            response = client.post(
                "/api/auth/login",
                json={
                    "username": "testuser",
                    "password": "testpass",
                },
            )
            assert response.status_code == 200, f"Login {i + 1} should succeed"

        # 第 6 次应该被限流
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpass",
            },
        )
        assert response.status_code == 429, f"Expected 429, got {response.status_code}"

    def test_login_rate_limit_blocks(self, client):
        """限流触发后阻止额外请求。"""
        # 先成功登录 5 次触发限流
        for i in range(5):
            response = client.post(
                "/api/auth/login",
                json={
                    "username": "testuser",
                    "password": "testpass",
                },
            )
            assert response.status_code == 200, f"Login {i + 1} should succeed"

        # 第 6 次应该被限流
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpass",
            },
        )
        assert response.status_code == 429
