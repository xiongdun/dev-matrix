"""Registry API 测试。

测试 Agent 和 Skill 注册表的列表、挂载、卸载、上传等功能。
需要认证才能访问受保护的路由。
"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agents.base import BaseAgent, Proposal, ValidationResult
from app.core.registry.agent_registry import agent_registry
from app.core.security import hash_password
from app.main import app
from app.skills.base import BaseSkill, SkillResult
from app.skills.registry import _global_registry as skill_registry
from app.state.models import Base, UserModel, get_db


class DummyAgent(BaseAgent):
    name = "dummy_agent"
    description = "A dummy agent for testing"

    async def generate_proposal(self, project_id, context):
        return Proposal(agent_name="dummy_agent", content="proposal")

    async def validate_output(self, project_id, proposal):
        return ValidationResult(is_valid=True)


class DummySkill(BaseSkill):
    name = "dummy_skill"
    description = "A dummy skill for testing"

    async def execute(self, context):
        return SkillResult(output="ok")


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
def auth_token(client):
    """获取认证 Token。"""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "testpass",
        },
    )
    assert response.status_code == 200
    return response.json()["token"]


@pytest.fixture(autouse=True)
def clean_registries():
    original_agents = agent_registry.list().copy()
    original_skills = skill_registry.list().copy()
    agent_registry._items.clear()
    skill_registry._items.clear()
    yield
    agent_registry._items.clear()
    agent_registry._items.update(original_agents)
    skill_registry._items.clear()
    skill_registry._items.update(original_skills)


def _auth_headers(token: str):
    """生成带认证 Token 的请求头。"""
    return {"Authorization": f"Bearer {token}"}


class TestAPIRegistry:
    def test_list_agents(self, client, auth_token):
        agent_registry.register("dummy_agent", DummyAgent)
        response = client.get("/api/registry/agents", headers=_auth_headers(auth_token))
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 1
        assert data["agents"][0]["name"] == "dummy_agent"

    def test_list_skills(self, client, auth_token):
        skill_registry.register("dummy_skill", DummySkill)
        response = client.get("/api/registry/skills", headers=_auth_headers(auth_token))
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        # 应用启动时自动发现了内置 skills，所以列表不止 1 个
        skill_names = [s["name"] for s in data["skills"]]
        assert "dummy_skill" in skill_names

    def test_mount_skill(self, client, auth_token):
        agent_registry.register("dummy_agent", DummyAgent)
        skill_registry.register("dummy_skill", DummySkill)
        response = client.post(
            "/api/registry/agents/dummy_agent/skills/dummy_skill",
            headers=_auth_headers(auth_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent"] == "dummy_agent"
        assert data["skill"] == "dummy_skill"

    def test_mount_skill_already_mounted(self, client, auth_token):
        agent_registry.register("dummy_agent", DummyAgent)
        skill_registry.register("dummy_skill", DummySkill)
        client.post(
            "/api/registry/agents/dummy_agent/skills/dummy_skill",
            headers=_auth_headers(auth_token),
        )
        response = client.post(
            "/api/registry/agents/dummy_agent/skills/dummy_skill",
            headers=_auth_headers(auth_token),
        )
        assert response.status_code == 409
        assert "already mounted" in response.json()["detail"]

    def test_unmount_skill(self, client, auth_token):
        agent_registry.register("dummy_agent", DummyAgent)
        skill_registry.register("dummy_skill", DummySkill)
        client.post(
            "/api/registry/agents/dummy_agent/skills/dummy_skill",
            headers=_auth_headers(auth_token),
        )
        response = client.delete(
            "/api/registry/agents/dummy_agent/skills/dummy_skill",
            headers=_auth_headers(auth_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent"] == "dummy_agent"
        assert data["skill"] == "dummy_skill"

    def test_unmount_skill_not_mounted(self, client, auth_token):
        agent_registry.register("dummy_agent", DummyAgent)
        skill_registry.register("dummy_skill", DummySkill)
        response = client.delete(
            "/api/registry/agents/dummy_agent/skills/dummy_skill",
            headers=_auth_headers(auth_token),
        )
        assert response.status_code == 404
        assert "not mounted" in response.json()["detail"]

    def test_upload_skill(self, client, auth_token, tmp_path, monkeypatch):
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        monkeypatch.setattr(
            "app.api.registry.os.path.dirname",
            lambda p: str(tmp_path),
        )

        code = """
from app.skills.base import BaseSkill, SkillResult

class UploadedSkill(BaseSkill):
    name = "uploaded_skill"
    description = "An uploaded skill"

    async def execute(self, context):
        return SkillResult(output="uploaded")
"""
        payload = {
            "name": "uploaded_skill",
            "description": "An uploaded skill",
            "code": code,
            "config": {},
        }
        response = client.post(
            "/api/registry/skills/upload",
            json=payload,
            headers=_auth_headers(auth_token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["name"] == "uploaded_skill"

    def test_upload_skill_duplicate(self, client, auth_token, tmp_path, monkeypatch):
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        monkeypatch.setattr(
            "app.api.registry.os.path.dirname",
            lambda p: str(tmp_path),
        )

        code = """
from app.skills.base import BaseSkill, SkillResult

class UploadedSkill(BaseSkill):
    name = "dup_skill"
    description = "Dup"

    async def execute(self, context):
        return SkillResult(output="dup")
"""
        payload = {
            "name": "dup_skill",
            "description": "Dup",
            "code": code,
            "config": {},
        }
        response1 = client.post(
            "/api/registry/skills/upload",
            json=payload,
            headers=_auth_headers(auth_token),
        )
        assert response1.status_code == 200

        response2 = client.post(
            "/api/registry/skills/upload",
            json=payload,
            headers=_auth_headers(auth_token),
        )
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    def test_upload_skill_invalid_code(self, client, auth_token):
        payload = {
            "name": "bad_skill",
            "description": "Bad",
            "code": "invalid python {{{",
            "config": {},
        }
        response = client.post(
            "/api/registry/skills/upload",
            json=payload,
            headers=_auth_headers(auth_token),
        )
        assert response.status_code in (400, 500)

    def test_upload_skill_no_base_skill(self, client, auth_token, tmp_path, monkeypatch):
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        monkeypatch.setattr(
            "app.api.registry.os.path.dirname",
            lambda p: str(tmp_path),
        )

        code = """
class NotASkill:
    pass
"""
        payload = {
            "name": "no_base_skill",
            "description": "No base",
            "code": code,
            "config": {},
        }
        response = client.post(
            "/api/registry/skills/upload",
            json=payload,
            headers=_auth_headers(auth_token),
        )
        assert response.status_code == 400
        assert "No class extending BaseSkill" in response.json()["detail"]

    def test_upload_skill_forbidden_pattern(self, client, auth_token):
        payload = {
            "name": "evil_skill",
            "description": "Evil",
            "code": "import os\nos.system('rm -rf /')",
            "config": {},
        }
        response = client.post(
            "/api/registry/skills/upload",
            json=payload,
            headers=_auth_headers(auth_token),
        )
        assert response.status_code == 400
        assert "forbidden pattern" in response.json()["detail"].lower()
