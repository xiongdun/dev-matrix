import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.api.registry import router as registry_router
from app.core.registry.agent_registry import agent_registry
from app.skills.registry import _global_registry as skill_registry
from app.agents.base import BaseAgent, Proposal, ValidationResult
from app.skills.base import BaseSkill, SkillResult


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
def client():
    return TestClient(app)


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


class TestAPIRegistry:
    def test_list_agents(self, client, clean_registries):
        agent_registry.register("dummy_agent", DummyAgent)
        response = client.get("/registry/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 1
        assert data["agents"][0]["name"] == "dummy_agent"

    def test_list_skills(self, client, clean_registries):
        skill_registry.register("dummy_skill", DummySkill)
        response = client.get("/registry/skills")
        assert response.status_code == 200
        data = response.json()
        assert "skills" in data
        assert len(data["skills"]) == 1
        assert data["skills"][0]["name"] == "dummy_skill"

    def test_mount_skill(self, client, clean_registries):
        agent_registry.register("dummy_agent", DummyAgent)
        skill_registry.register("dummy_skill", DummySkill)
        response = client.post("/registry/agents/dummy_agent/skills/dummy_skill")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent"] == "dummy_agent"
        assert data["skill"] == "dummy_skill"

    def test_mount_skill_already_mounted(self, client, clean_registries):
        agent_registry.register("dummy_agent", DummyAgent)
        skill_registry.register("dummy_skill", DummySkill)
        client.post("/registry/agents/dummy_agent/skills/dummy_skill")
        response = client.post("/registry/agents/dummy_agent/skills/dummy_skill")
        assert response.status_code == 409
        assert "already mounted" in response.json()["detail"]

    def test_unmount_skill(self, client, clean_registries):
        agent_registry.register("dummy_agent", DummyAgent)
        skill_registry.register("dummy_skill", DummySkill)
        client.post("/registry/agents/dummy_agent/skills/dummy_skill")
        response = client.delete("/registry/agents/dummy_agent/skills/dummy_skill")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["agent"] == "dummy_agent"
        assert data["skill"] == "dummy_skill"

    def test_unmount_skill_not_mounted(self, client, clean_registries):
        agent_registry.register("dummy_agent", DummyAgent)
        skill_registry.register("dummy_skill", DummySkill)
        response = client.delete("/registry/agents/dummy_agent/skills/dummy_skill")
        assert response.status_code == 404
        assert "not mounted" in response.json()["detail"]

    def test_upload_skill(self, client, clean_registries, tmp_path, monkeypatch):
        import os
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
        response = client.post("/registry/skills/upload", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["name"] == "uploaded_skill"

    def test_upload_skill_duplicate(self, client, clean_registries, tmp_path, monkeypatch):
        import os
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
        response1 = client.post("/registry/skills/upload", json=payload)
        assert response1.status_code == 200

        response2 = client.post("/registry/skills/upload", json=payload)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"]

    def test_upload_skill_invalid_code(self, client, clean_registries):
        payload = {
            "name": "bad_skill",
            "description": "Bad",
            "code": "invalid python {{{",
            "config": {},
        }
        response = client.post("/registry/skills/upload", json=payload)
        assert response.status_code in (400, 500)

    def test_upload_skill_no_base_skill(self, client, clean_registries, tmp_path, monkeypatch):
        import os
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
        response = client.post("/registry/skills/upload", json=payload)
        assert response.status_code == 400
        assert "No class extending BaseSkill" in response.json()["detail"]

    def test_upload_skill_forbidden_pattern(self, client, clean_registries):
        payload = {
            "name": "evil_skill",
            "description": "Evil",
            "code": "import os\nos.system('rm -rf /')",
            "config": {},
        }
        response = client.post("/registry/skills/upload", json=payload)
        assert response.status_code == 400
        assert "forbidden pattern" in response.json()["detail"].lower()
