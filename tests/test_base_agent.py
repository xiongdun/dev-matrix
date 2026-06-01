import pytest

from app.agents.base import BaseAgent, Proposal, ValidationResult
from app.skills.base import BaseSkill, SkillConfig, SkillResult


class MockLLMRouter:
    async def complete(self, prompt, **kwargs):
        return "mock response"


class MockStateRepo:
    def get_state(self, project_id):
        return None

    def update_state(self, **kwargs):
        pass


class DummySkill(BaseSkill):
    name = "dummy_skill"
    description = "A dummy skill for testing"

    async def execute(self, context):
        return SkillResult(output="dummy_result")


class FailingSkill(BaseSkill):
    name = "failing_skill"

    async def execute(self, context):
        raise RuntimeError("skill failure")


class TestAgent(BaseAgent):
    name = "test"
    description = "Test agent"

    async def generate_proposal(self, project_id, context):
        return Proposal(agent_name="test", content="test proposal")

    async def validate_output(self, project_id, proposal):
        return ValidationResult(is_valid=True)


class TestBaseAgent:
    def test_use_skill(self):
        agent = TestAgent(MockLLMRouter(), MockStateRepo())
        skill = DummySkill()
        result = agent.use_skill(skill)
        assert result is agent
        assert agent.has_skill("dummy_skill")

    def test_has_skill(self):
        agent = TestAgent(MockLLMRouter(), MockStateRepo())
        assert not agent.has_skill("dummy_skill")
        agent.use_skill(DummySkill())
        assert agent.has_skill("dummy_skill")
        assert not agent.has_skill("nonexistent")

    @pytest.mark.asyncio
    async def test_call_skill(self):
        agent = TestAgent(MockLLMRouter(), MockStateRepo())
        agent.use_skill(DummySkill())
        result = await agent.call_skill("dummy_skill", {"key": "value"})
        assert isinstance(result, SkillResult)
        assert result.output == "dummy_result"

    @pytest.mark.asyncio
    async def test_call_skill_not_found(self):
        agent = TestAgent(MockLLMRouter(), MockStateRepo())
        with pytest.raises(ValueError, match="Skill 'missing' not composed into agent 'test'"):
            await agent.call_skill("missing", {})

    def test_list_skills(self):
        agent = TestAgent(MockLLMRouter(), MockStateRepo())
        assert agent.list_skills() == []
        agent.use_skill(DummySkill())
        assert agent.list_skills() == ["dummy_skill"]

    def test_unmount_skill(self):
        agent = TestAgent(MockLLMRouter(), MockStateRepo())
        skill = DummySkill()
        agent.use_skill(skill)
        assert agent.has_skill("dummy_skill")
        del agent._skills["dummy_skill"]
        assert not agent.has_skill("dummy_skill")

    @pytest.mark.asyncio
    async def test_call_skill_timeout(self, monkeypatch):
        import app.agents.base as agent_base_module

        monkeypatch.setattr(agent_base_module, "DEFAULT_SKILL_TIMEOUT", 0.01)

        agent = TestAgent(MockLLMRouter(), MockStateRepo())

        class SlowSkill(BaseSkill):
            name = "slow_skill"

            async def execute(self, context):
                import asyncio

                await asyncio.sleep(10)
                return SkillResult(output="too late")

        skill = SlowSkill()
        skill.config = SkillConfig(timeout=0.01)
        agent.use_skill(skill)
        with pytest.raises(TimeoutError, match="Skill 'slow_skill' execution timed out"):
            await agent.call_skill("slow_skill", {})

    @pytest.mark.asyncio
    async def test_call_skill_execution_error(self):
        agent = TestAgent(MockLLMRouter(), MockStateRepo())
        agent.use_skill(FailingSkill())
        with pytest.raises(RuntimeError, match="skill failure"):
            await agent.call_skill("failing_skill", {})
