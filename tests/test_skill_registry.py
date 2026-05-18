from app.skills.base import BaseSkill, SkillResult, SkillConfig
from app.skills.registry import SkillRegistry, register_skill


class TestSkillRegistry:
    def test_discover_skills(self):
        reg = SkillRegistry()
        discovered = reg.discover("app.skills")
        assert isinstance(discovered, dict)
        assert len(discovered) > 0

    def test_create_skill(self):
        reg = SkillRegistry()

        class MySkill(BaseSkill):
            name = "my_skill"
            description = "A test skill"

            async def execute(self, context):
                return SkillResult(output="done")

        reg.register("my_skill", MySkill)
        instance = reg.create("my_skill")
        assert isinstance(instance, BaseSkill)
        assert instance.name == "my_skill"
        assert isinstance(instance.config, SkillConfig)

    def test_create_skill_with_config(self):
        reg = SkillRegistry()

        class ConfiguredSkill(BaseSkill):
            name = "configured_skill"

            async def execute(self, context):
                return SkillResult(output="configured")

        reg.register("configured_skill", ConfiguredSkill)
        config = SkillConfig(timeout=60, retry_count=3)
        instance = reg.create("configured_skill", config=config)
        assert instance.config.timeout == 60
        assert instance.config.retry_count == 3

    def test_register_skill_decorator(self):
        reg = SkillRegistry()

        @register_skill("decorated_skill", registry=reg)
        class DecoratedSkill(BaseSkill):
            name = "decorated_skill"

            async def execute(self, context):
                return SkillResult(output="decorated")

        assert reg.exists("decorated_skill")
        cls = reg.get("decorated_skill")
        assert cls is DecoratedSkill

    def test_register_skill_decorator_default_name(self):
        reg = SkillRegistry()

        @register_skill(registry=reg)
        class DefaultNameSkill(BaseSkill):
            name = "default_name_skill"

            async def execute(self, context):
                return SkillResult(output="default")

        assert reg.exists("default_name_skill")
