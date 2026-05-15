import pytest

from app.skills.base import BaseSkill, SkillResult, SkillConfig


class ConcreteSkill(BaseSkill):
    name = "concrete_skill"
    description = "A concrete skill for testing"

    async def execute(self, context):
        return SkillResult(output="executed", metadata={"key": "value"})


class FailingSkill(BaseSkill):
    name = "failing_skill"

    async def execute(self, context):
        raise RuntimeError("execution failed")


class UnhealthySkill(BaseSkill):
    name = "unhealthy_skill"

    def health_check(self):
        return False

    async def execute(self, context):
        return SkillResult(output="ok")


class TestBaseSkill:
    @pytest.mark.asyncio
    async def test_execute(self):
        skill = ConcreteSkill()
        result = await skill.execute({"input": "test"})
        assert isinstance(result, SkillResult)
        assert result.output == "executed"
        assert result.metadata == {"key": "value"}
        assert result.success is True
        assert result.error is None

    def test_health_check(self):
        healthy = ConcreteSkill()
        assert healthy.health_check() is True

        unhealthy = UnhealthySkill()
        assert unhealthy.health_check() is False

    def test_to_dict(self):
        skill = ConcreteSkill(config=SkillConfig(timeout=60, retry_count=2))
        data = skill.to_dict()
        assert data["name"] == "concrete_skill"
        assert data["description"] == "A concrete skill for testing"
        assert data["config"]["timeout"] == 60
        assert data["config"]["retry_count"] == 2

    def test_to_dict_defaults(self):
        skill = ConcreteSkill()
        data = skill.to_dict()
        assert data["config"]["timeout"] == 30
        assert data["config"]["retry_count"] == 0

    @pytest.mark.asyncio
    async def test_execute_with_timeout_success(self):
        skill = ConcreteSkill()
        result = await skill.execute_with_timeout({"input": "test"})
        assert isinstance(result, SkillResult)
        assert result.output == "executed"
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_with_timeout_timeout(self, monkeypatch):
        import app.skills.base as base_module
        monkeypatch.setattr(base_module, "DEFAULT_SKILL_TIMEOUT", 0.01)

        class SlowSkill(BaseSkill):
            name = "slow_skill"

            async def execute(self, context):
                import asyncio
                await asyncio.sleep(10)
                return SkillResult(output="too late")

        skill = SlowSkill()
        skill.config = SkillConfig(timeout=0.01)
        result = await skill.execute_with_timeout({})
        assert result.success is False
        assert "timed out" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_timeout_exception(self):
        skill = FailingSkill()
        result = await skill.execute_with_timeout({})
        assert result.success is False
        assert "execution failed" in result.error

    def test_default_config(self):
        skill = ConcreteSkill()
        assert isinstance(skill.config, SkillConfig)
        assert skill.config.timeout == 30
        assert skill.config.retry_count == 0
        assert skill.config.parameters == {}

    def test_custom_config(self):
        config = SkillConfig(timeout=120, retry_count=5, parameters={"model": "gpt-4"})
        skill = ConcreteSkill(config=config)
        assert skill.config.timeout == 120
        assert skill.config.retry_count == 5
        assert skill.config.parameters == {"model": "gpt-4"}
