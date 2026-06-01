import pytest

from app.agents.base import BaseAgent, Proposal
from app.skills.base import BaseSkill, SkillConfig, SkillResult
from app.skills.registry import SkillRegistry, register_skill


class TestSkillBase:
    def test_skill_result_creation(self):
        result = SkillResult(output="test", metadata={"key": "value"})
        assert result.output == "test"
        assert result.metadata == {"key": "value"}

    def test_skill_config_defaults(self):
        config = SkillConfig()
        assert config.timeout == 30
        assert config.retry_count == 0

    def test_base_skill_cannot_execute(self):
        class DummySkill(BaseSkill):
            name = "dummy"

            async def execute(self, context):
                return await super().execute(context)

        skill = DummySkill()
        with pytest.raises(NotImplementedError):
            import asyncio

            asyncio.run(skill.execute({}))


class TestSkillRegistry:
    def test_register_and_get(self):
        reg = SkillRegistry()

        @register_skill("test_skill", registry=reg)
        class TestSkill(BaseSkill):
            name = "test_skill"

            async def execute(self, context):
                return SkillResult(output="ok")

        assert reg.exists("test_skill")
        skill_class = reg.get("test_skill")
        assert skill_class.name == "test_skill"

    def test_create_instance(self):
        reg = SkillRegistry()

        @register_skill("my_skill", registry=reg)
        class MySkill(BaseSkill):
            name = "my_skill"

            async def execute(self, context):
                return SkillResult(output="done")

        instance = reg.create("my_skill")
        assert isinstance(instance, BaseSkill)
        assert instance.name == "my_skill"

    def test_list_skills(self):
        reg = SkillRegistry()

        @register_skill("skill_a", registry=reg)
        class SkillA(BaseSkill):
            name = "skill_a"

            async def execute(self, context):
                return SkillResult(output="a")

        @register_skill("skill_b", registry=reg)
        class SkillB(BaseSkill):
            name = "skill_b"

            async def execute(self, context):
                return SkillResult(output="b")

        skills = reg.list()
        assert "skill_a" in skills
        assert "skill_b" in skills


class TestConcreteSkills:
    @pytest.mark.asyncio
    async def test_code_search_skill(self):
        from app.skills.code_search import CodeSearchSkill

        skill = CodeSearchSkill()
        result = await skill.execute({"query": "test", "repo_path": "."})
        assert isinstance(result, SkillResult)

    @pytest.mark.asyncio
    async def test_prompt_enhance_skill(self):
        from app.skills.prompt_enhance import PromptEnhanceSkill

        skill = PromptEnhanceSkill()
        result = await skill.execute({"prompt": "write code", "context": {}})
        assert isinstance(result, SkillResult)
        assert result.output

    @pytest.mark.asyncio
    async def test_validation_skill(self):
        from app.skills.validation import ValidationSkill

        skill = ValidationSkill()
        result = await skill.execute(
            {
                "content": "functional requirements\nacceptance criteria",
                "rules": ["functional", "acceptance"],
            }
        )
        assert isinstance(result, SkillResult)
        assert "valid" in result.output


class MockLLMRouter:
    async def complete(self, prompt, **kwargs):
        return "mock response"


class MockStateRepo:
    def get_state(self, project_id):
        return None

    def update_state(self, **kwargs):
        pass


class TestAgentSkillComposition:
    def test_agent_can_use_skill(self):
        from app.skills.validation import ValidationSkill

        class TestAgent(BaseAgent):
            name = "test"

            async def generate_proposal(self, project_id, context):
                return Proposal(agent_name="test", content="test")

            async def validate_output(self, project_id, proposal):
                from app.agents.base import ValidationResult

                return ValidationResult(is_valid=True)

        agent = TestAgent(MockLLMRouter(), MockStateRepo())
        skill = ValidationSkill()
        agent.use_skill(skill)

        assert "validation" in agent._skills

    @pytest.mark.asyncio
    async def test_agent_can_call_skill(self):
        from app.skills.validation import ValidationSkill

        class TestAgent(BaseAgent):
            name = "test"

            async def generate_proposal(self, project_id, context):
                return Proposal(agent_name="test", content="test")

            async def validate_output(self, project_id, proposal):
                from app.agents.base import ValidationResult

                return ValidationResult(is_valid=True)

        agent = TestAgent(MockLLMRouter(), MockStateRepo())
        skill = ValidationSkill()
        agent.use_skill(skill)

        result = await agent.call_skill(
            "validation",
            {"content": "functional requirements", "rules": ["functional"]},
        )
        assert result.success


class TestArchitectAgentWithSkills:
    @pytest.mark.asyncio
    async def test_architect_uses_code_search_skill(self):
        from app.agents.architect import ArchitectAgent

        agent = ArchitectAgent(MockLLMRouter(), MockStateRepo())
        from app.skills.code_search import CodeSearchSkill

        agent.use_skill(CodeSearchSkill())

        assert agent.has_skill("code_search")

        result = await agent.call_skill("code_search", {"query": "auth", "repo_path": "."})
        assert isinstance(result, SkillResult)


class TestSkillIntegration:
    @pytest.mark.asyncio
    async def test_skill_standalone_execution(self):
        """Skill can run independently without Agent."""
        from app.skills.validation import ValidationSkill

        skill = ValidationSkill()
        result = await skill.execute(
            {
                "content": "functional requirements\nacceptance criteria",
                "rules": ["functional", "acceptance"],
            }
        )
        assert result.success
        assert result.output["valid"] is True

    @pytest.mark.asyncio
    async def test_skill_composed_with_agent(self):
        """Skill can be composed with Agent to enhance capabilities."""
        from app.skills.prompt_enhance import PromptEnhanceSkill

        class TestAgent(BaseAgent):
            name = "test"

            async def generate_proposal(self, project_id, context):
                if self.has_skill("prompt_enhance"):
                    result = await self.call_skill(
                        "prompt_enhance",
                        {
                            "prompt": context.get("task", ""),
                            "context": {"language": "python"},
                        },
                    )
                    enhanced = result.output
                else:
                    enhanced = context.get("task", "")
                return Proposal(agent_name="test", content=enhanced)

            async def validate_output(self, project_id, proposal):
                from app.agents.base import ValidationResult

                return ValidationResult(is_valid=True)

        agent = TestAgent(MockLLMRouter(), MockStateRepo())
        agent.use_skill(PromptEnhanceSkill())

        proposal = await agent.generate_proposal("p1", {"task": "write a function"})
        assert "python" in proposal.content.lower()
        assert "expert" in proposal.content.lower()
