# Agent-Skill Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce a pluggable Skill system where Skills are independent, reusable capability units that can be executed standalone or composed with Agents to enhance their capabilities.

**Architecture:** Skills are self-contained units with their own configuration and execution logic. Agents retain their core `generate_proposal`/`validate_output` methods but can optionally compose Skills to augment their behavior. A global `SkillRegistry` enables runtime discovery and instantiation.

**Tech Stack:** Python 3.11, existing FastAPI/Temporal stack, pytest for testing

---

## File Structure

### New Files
- `app/skills/__init__.py` — Package exports
- `app/skills/base.py` — `BaseSkill` abstract class, `SkillResult`, `SkillConfig`
- `app/skills/registry.py` — `SkillRegistry` with decorator-based registration
- `app/skills/code_search.py` — Code search skill (uses code_intelligence)
- `app/skills/prompt_enhance.py` — Prompt enhancement skill
- `app/skills/validation.py` — Output validation skill
- `tests/test_skills.py` — Skill system tests

### Modified Files
- `app/agents/base.py` — Add Skill composition support (`use_skill`, `call_skill`)
- `app/agents/architect.py` — Demonstrate Skill usage
- `app/core/registry/__init__.py` — Export discovery utility
- `app/workflow/activities.py` — Reuse LLMRouter and Agent instances

---

## Task 1: Skill Base Classes

**Files:**
- Create: `app/skills/base.py`
- Create: `app/skills/__init__.py`

- [ ] **Step 1: Write the failing test**

`tests/test_skills.py`:
```python
import pytest
from app.skills.base import BaseSkill, SkillResult, SkillConfig

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

        skill = DummySkill()
        with pytest.raises(NotImplementedError):
            import asyncio
            asyncio.run(skill.execute({}))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/Summer/Documents/works/codes/dev-matrix && python3 -m pytest tests/test_skills.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.skills'"

- [ ] **Step 3: Implement Skill base classes**

`app/skills/base.py`:
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SkillResult:
    output: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


@dataclass
class SkillConfig:
    timeout: int = 30
    retry_count: int = 0
    parameters: Dict[str, Any] = field(default_factory=dict)


class BaseSkill(ABC):
    name: str = "base"
    description: str = ""

    def __init__(self, config: Optional[SkillConfig] = None):
        self.config = config or SkillConfig()

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> SkillResult:
        pass

    def health_check(self) -> bool:
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "config": {
                "timeout": self.config.timeout,
                "retry_count": self.config.retry_count,
            },
        }
```

`app/skills/__init__.py`:
```python
from app.skills.base import BaseSkill, SkillResult, SkillConfig

__all__ = ["BaseSkill", "SkillResult", "SkillConfig"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/Summer/Documents/works/codes/dev-matrix && python3 -m pytest tests/test_skills.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/Summer/Documents/works/codes/dev-matrix
git add app/skills/ tests/test_skills.py
git commit -m "feat(skills): add BaseSkill, SkillResult, SkillConfig"
```

---

## Task 2: Skill Registry with Decorator Registration

**Files:**
- Create: `app/skills/registry.py`
- Modify: `app/skills/__init__.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_skills.py`:
```python
from app.skills.registry import SkillRegistry, register_skill

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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_skills.py::TestSkillRegistry -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.skills.registry'"

- [ ] **Step 3: Implement SkillRegistry**

`app/skills/registry.py`:
```python
from typing import Dict, Optional, Type

from app.core.registry.base import Registry
from app.skills.base import BaseSkill, SkillConfig


class SkillRegistry(Registry[BaseSkill]):
    def create(self, name: str, config: Optional[SkillConfig] = None) -> BaseSkill:
        skill_class = self.get(name)
        return skill_class(config)

    def discover(self, package: str = "app.skills") -> Dict[str, Type[BaseSkill]]:
        from app.core.registry.discovery import discover_and_register
        return discover_and_register(package, self, BaseSkill)


def register_skill(name: str = None, registry: SkillRegistry = None):
    def decorator(cls: Type[BaseSkill]) -> Type[BaseSkill]:
        reg = registry or _global_registry
        reg.register(name or cls.name, cls)
        return cls
    return decorator


_global_registry = SkillRegistry()
```

Modify `app/skills/__init__.py`:
```python
from app.skills.base import BaseSkill, SkillResult, SkillConfig
from app.skills.registry import SkillRegistry, register_skill

__all__ = ["BaseSkill", "SkillResult", "SkillConfig", "SkillRegistry", "register_skill"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_skills.py::TestSkillRegistry -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/skills/registry.py app/skills/__init__.py tests/test_skills.py
git commit -m "feat(skills): add SkillRegistry with decorator registration"
```

---

## Task 3: Concrete Skills

**Files:**
- Create: `app/skills/code_search.py`
- Create: `app/skills/prompt_enhance.py`
- Create: `app/skills/validation.py`

- [ ] **Step 1: Write tests for concrete skills**

Add to `tests/test_skills.py`:
```python
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
        assert "enhanced" in result.metadata or result.output

    @pytest.mark.asyncio
    async def test_validation_skill(self):
        from app.skills.validation import ValidationSkill
        skill = ValidationSkill()
        result = await skill.execute({
            "content": "functional requirements\nacceptance criteria",
            "rules": ["functional", "acceptance"]
        })
        assert isinstance(result, SkillResult)
        assert "valid" in result.metadata
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_skills.py::TestConcreteSkills -v`
Expected: FAIL with import errors

- [ ] **Step 3: Implement concrete skills**

`app/skills/code_search.py`:
```python
from typing import Any, Dict

from app.skills.base import BaseSkill, SkillResult


class CodeSearchSkill(BaseSkill):
    name = "code_search"
    description = "Search codebase for relevant files and functions"

    async def execute(self, context: Dict[str, Any]) -> SkillResult:
        query = context.get("query", "")
        repo_path = context.get("repo_path", ".")

        try:
            from app.code_intelligence.indexer import CodeIndexer
            from app.code_intelligence.retriever import CodeRetriever

            indexer = CodeIndexer(root_path=repo_path)
            indexer.index()

            retriever = CodeRetriever(indexer)
            results = retriever.search(query, top_k=5)

            return SkillResult(
                output=results,
                metadata={"query": query, "result_count": len(results)},
            )
        except Exception as e:
            return SkillResult(
                output=[],
                success=False,
                error=str(e),
                metadata={"query": query},
            )
```

`app/skills/prompt_enhance.py`:
```python
from typing import Any, Dict

from app.skills.base import BaseSkill, SkillResult


class PromptEnhanceSkill(BaseSkill):
    name = "prompt_enhance"
    description = "Enhance prompts with additional context and structure"

    async def execute(self, context: Dict[str, Any]) -> SkillResult:
        prompt = context.get("prompt", "")
        extra_context = context.get("context", {})

        enhanced = self._enhance(prompt, extra_context)

        return SkillResult(
            output=enhanced,
            metadata={"original_length": len(prompt), "enhanced_length": len(enhanced)},
        )

    def _enhance(self, prompt: str, context: Dict[str, Any]) -> str:
        parts = ["You are an expert software engineer."]

        if "language" in context:
            parts.append(f"Primary language: {context['language']}.")
        if "framework" in context:
            parts.append(f"Framework: {context['framework']}.")
        if "style_guide" in context:
            parts.append(f"Follow style guide: {context['style_guide']}.")

        parts.append("\n--- Task ---\n")
        parts.append(prompt)
        parts.append("\n--- Instructions ---\n")
        parts.append("Provide clear, well-structured, production-ready output.")

        return "\n".join(parts)
```

`app/skills/validation.py`:
```python
from typing import Any, Dict, List

from app.skills.base import BaseSkill, SkillResult


class ValidationSkill(BaseSkill):
    name = "validation"
    description = "Validate content against a set of rules"

    async def execute(self, context: Dict[str, Any]) -> SkillResult:
        content = context.get("content", "")
        rules = context.get("rules", [])
        content_lower = content.lower()

        errors = []
        for rule in rules:
            if rule.lower() not in content_lower:
                errors.append(f"Missing required section: {rule}")

        return SkillResult(
            output={"valid": len(errors) == 0, "errors": errors},
            metadata={"rule_count": len(rules), "error_count": len(errors)},
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_skills.py::TestConcreteSkills -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/skills/code_search.py app/skills/prompt_enhance.py app/skills/validation.py tests/test_skills.py
git commit -m "feat(skills): add concrete skills - code_search, prompt_enhance, validation"
```

---

## Task 4: Refactor BaseAgent for Skill Composition

**Files:**
- Modify: `app/agents/base.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_skills.py`:
```python
from app.agents.base import BaseAgent, Proposal
from app.llm.router import LLMRouter
from app.state.repository import StateRepository

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

        result = await agent.call_skill("validation", {
            "content": "functional requirements",
            "rules": ["functional"]
        })
        assert result.success
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_skills.py::TestAgentSkillComposition -v`
Expected: FAIL with "AttributeError: 'BaseAgent' object has no attribute 'use_skill'"

- [ ] **Step 3: Refactor BaseAgent**

`app/agents/base.py` (modify existing):
```python
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.llm.router import LLMRouter
from app.state.repository import StateRepository


@dataclass
class Proposal:
    agent_name: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class BaseAgent(ABC):
    name: str = "base"
    description: str = "Base agent"

    def __init__(
        self,
        llm_router: LLMRouter,
        state_repository: StateRepository,
    ):
        self.llm_router = llm_router
        self.state_repository = state_repository
        self._skills: Dict[str, "BaseSkill"] = {}

    def read_state(self, project_id: str) -> Dict[str, Any]:
        state = self.state_repository.get_state(project_id)
        if state is None or not state.state_json:
            return {}
        return json.loads(state.state_json)

    def write_state(self, project_id: str, state_dict: Dict[str, Any], status: Optional[str] = None):
        self.state_repository.update_state(
            project_id=project_id,
            state_json=json.dumps(state_dict, ensure_ascii=False),
            status=status,
        )

    @abstractmethod
    async def generate_proposal(self, project_id: str, context: Dict[str, Any]) -> Proposal:
        pass

    @abstractmethod
    async def validate_output(self, project_id: str, proposal: Proposal) -> ValidationResult:
        pass

    async def run(self, project_id: str, context: Dict[str, Any]) -> Proposal:
        proposal = await self.generate_proposal(project_id, context)
        validation = await self.validate_output(project_id, proposal)
        if not validation.is_valid:
            raise ValueError(f"Validation failed: {validation.errors}")
        return proposal

    # ===== Skill Composition API =====

    def use_skill(self, skill: "BaseSkill") -> "BaseAgent":
        """Compose a Skill into this Agent. Returns self for chaining."""
        self._skills[skill.name] = skill
        return self

    def has_skill(self, name: str) -> bool:
        return name in self._skills

    async def call_skill(self, name: str, context: Dict[str, Any]) -> "SkillResult":
        """Execute a composed Skill by name."""
        from app.skills.base import BaseSkill
        skill = self._skills.get(name)
        if skill is None:
            raise ValueError(f"Skill '{name}' not composed into agent '{self.name}'")
        return await skill.execute(context)

    def list_skills(self) -> List[str]:
        return list(self._skills.keys())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_skills.py::TestAgentSkillComposition -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/agents/base.py tests/test_skills.py
git commit -m "feat(agents): add Skill composition API to BaseAgent"
```

---

## Task 5: Demonstrate Skill Usage in ArchitectAgent

**Files:**
- Modify: `app/agents/architect.py`

- [ ] **Step 1: Write the test**

Add to `tests/test_skills.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_skills.py::TestArchitectAgentWithSkills -v`
Expected: FAIL — ArchitectAgent doesn't use skills yet

- [ ] **Step 3: Update ArchitectAgent to demonstrate Skill usage**

`app/agents/architect.py`:
```python
from typing import Any, Dict

from app.agents.base import BaseAgent, Proposal, ValidationResult


class ArchitectAgent(BaseAgent):
    name = "architect"
    description = "Performs code impact analysis and designs technical solutions"

    async def generate_proposal(self, project_id: str, context: Dict[str, Any]) -> Proposal:
        state = self.read_state(project_id)
        prd = state.get("prd", "")
        repo_path = context.get("repo_path", "")

        # Use code_search skill if available
        code_context = ""
        if self.has_skill("code_search") and repo_path:
            try:
                result = await self.call_skill("code_search", {
                    "query": prd,
                    "repo_path": repo_path,
                })
                if result.success:
                    code_context = f"\n\nRelevant code context:\n{result.output}"
            except Exception:
                pass

        prompt = (
            f"You are a Software Architect. Based on the following PRD, analyze the "
            f"technical impact and design a solution. Include: system design, "
            f"component diagram, API design, data model changes, and affected files."
            f"{code_context}\n\n"
            f"PRD:\n{prd}\n\n"
            f"Repository: {repo_path}"
        )
        response = await self.llm_router.complete(prompt)
        return Proposal(
            agent_name=self.name,
            content=response,
            metadata={"phase": "architecture_design", "used_code_search": bool(code_context)},
        )

    async def validate_output(self, project_id: str, proposal: Proposal) -> ValidationResult:
        content = proposal.content.lower()
        errors = []
        if "design" not in content:
            errors.append("Missing design section")
        if "api" not in content:
            errors.append("Missing API design")
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_skills.py::TestArchitectAgentWithSkills -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/agents/architect.py tests/test_skills.py
git commit -m "feat(agents): ArchitectAgent demonstrates code_search Skill usage"
```

---

## Task 6: Reuse Agent and LLMRouter in Activities

**Files:**
- Modify: `app/workflow/activities.py`

- [ ] **Step 1: Analyze current code**

Current `activities.py` creates new `LLMRouter()` and Agent instances in every activity. We need to accept them as parameters or use a factory.

- [ ] **Step 2: Refactor activities to accept dependencies**

`app/workflow/activities.py` (key changes):
```python
from typing import Any, Dict

from app.agents.business_analyst import BusinessAnalystAgent
from app.agents.product_manager import ProductManagerAgent
from app.agents.architect import ArchitectAgent
from app.agents.developer import DeveloperAgent
from app.agents.qa import QAAgent
from app.events.bus import event_bus
from app.events.types import Event
from app.llm.router import LLMRouter
from app.state.repository import StateRepository
from app.utils.audit import AuditLogger, AuditLevel
from app.workflow.pipeline.executor import ActivityContext


audit_logger = AuditLogger()

# Global singletons for reuse within the worker process
_llm_router: LLMRouter = None
_state_repo: StateRepository = None


def _get_llm_router() -> LLMRouter:
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router


def _get_state_repo() -> StateRepository:
    global _state_repo
    if _state_repo is None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.config import get_settings
        from app.state.models import Base

        settings = get_settings()
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        _state_repo = StateRepository(db)
    return _state_repo


def _create_agent(agent_class, skills=None):
    """Factory: create agent with reused dependencies and optional skills."""
    agent = agent_class(
        llm_router=_get_llm_router(),
        state_repository=_get_state_repo(),
    )
    if skills:
        for skill in skills:
            agent.use_skill(skill)
    return agent


async def analyze_requirement(context: ActivityContext) -> Dict[str, Any]:
    requirement = context.inputs.get("requirement", "")
    if not requirement:
        raise ValueError("No requirement provided")

    agent = _create_agent(BusinessAnalystAgent)

    proposal = await agent.generate_proposal(
        project_id=context.project_id,
        context={"raw_input": requirement},
    )

    audit_logger.log_agent_action(
        agent_name="business_analyst",
        action="analyze_requirement",
        project_id=context.project_id,
        details={"proposal_length": len(proposal.content)},
    )

    event_bus.publish(Event(
        type="requirement.analyzed",
        payload={
            "project_id": context.project_id,
            "proposal": proposal.content,
        },
    ))

    return {
        "analysis": proposal.content,
        "metadata": proposal.metadata,
    }


async def generate_prd(context: ActivityContext) -> Dict[str, Any]:
    analysis = context.inputs.get("previous_output", {}).get("analysis", "")
    if not analysis:
        raise ValueError("No analysis provided")

    agent = _create_agent(ProductManagerAgent)

    proposal = await agent.generate_proposal(
        project_id=context.project_id,
        context={"analysis": analysis},
    )

    audit_logger.log_agent_action(
        agent_name="product_manager",
        action="generate_prd",
        project_id=context.project_id,
        details={"proposal_length": len(proposal.content)},
    )

    return {
        "prd": proposal.content,
        "metadata": proposal.metadata,
    }


async def analyze_code_impact(context: ActivityContext) -> Dict[str, Any]:
    prd = context.inputs.get("previous_output", {}).get("prd", "")
    if not prd:
        raise ValueError("No PRD provided")

    from app.skills.code_search import CodeSearchSkill
    agent = _create_agent(
        ArchitectAgent,
        skills=[CodeSearchSkill()] if context.inputs.get("repo_path") else None,
    )

    proposal = await agent.generate_proposal(
        project_id=context.project_id,
        context={"prd": prd, "repo_path": context.inputs.get("repo_path", "")},
    )

    audit_logger.log_agent_action(
        agent_name="architect",
        action="analyze_code_impact",
        project_id=context.project_id,
        details={"proposal_length": len(proposal.content)},
    )

    return {
        "architecture": proposal.content,
        "metadata": proposal.metadata,
    }


async def generate_patch(context: ActivityContext) -> Dict[str, Any]:
    architecture = context.inputs.get("previous_output", {}).get("architecture", "")
    if not architecture:
        raise ValueError("No architecture provided")

    agent = _create_agent(DeveloperAgent)

    proposal = await agent.generate_proposal(
        project_id=context.project_id,
        context={"architecture": architecture},
    )

    audit_logger.log_agent_action(
        agent_name="developer",
        action="generate_patch",
        project_id=context.project_id,
        details={"proposal_length": len(proposal.content)},
    )

    return {
        "patch": proposal.content,
        "metadata": proposal.metadata,
    }


async def generate_tests(context: ActivityContext) -> Dict[str, Any]:
    patch = context.inputs.get("previous_output", {}).get("patch", "")
    if not patch:
        raise ValueError("No patch provided")

    agent = _create_agent(QAAgent)

    proposal = await agent.generate_proposal(
        project_id=context.project_id,
        context={"patch": patch},
    )

    audit_logger.log_agent_action(
        agent_name="qa",
        action="generate_tests",
        project_id=context.project_id,
        details={"proposal_length": len(proposal.content)},
    )

    return {
        "tests": proposal.content,
        "metadata": proposal.metadata,
    }


async def execute_tests(context: ActivityContext) -> Dict[str, Any]:
    tests = context.inputs.get("previous_output", {}).get("tests", "")
    if not tests:
        raise ValueError("No tests provided")

    audit_logger.log_agent_action(
        agent_name="qa",
        action="execute_tests",
        project_id=context.project_id,
        details={"test_length": len(tests)},
    )

    return {
        "executed": True,
        "results": "Tests executed (placeholder implementation)",
    }


ACTIVITY_MAP = {
    "analyze_requirement": analyze_requirement,
    "generate_prd": generate_prd,
    "analyze_code_impact": analyze_code_impact,
    "generate_patch": generate_patch,
    "generate_tests": generate_tests,
    "execute_tests": execute_tests,
}
```

- [ ] **Step 3: Verify syntax**

Run: `python3 -m py_compile app/workflow/activities.py`
Expected: No output (success)

- [ ] **Step 4: Commit**

```bash
git add app/workflow/activities.py
git commit -m "refactor(activities): reuse LLMRouter and Agent instances, inject Skills"
```

---

## Task 7: Update Core Registry Exports

**Files:**
- Modify: `app/core/registry/__init__.py`

- [ ] **Step 1: Add discovery export**

`app/core/registry/__init__.py`:
```python
from app.core.registry.base import Registry, register_in
from app.core.registry.agent_registry import agent_registry, register_agent
from app.core.registry.llm_registry import llm_registry, register_llm_provider
from app.core.registry.discovery import discover_and_register

__all__ = [
    "Registry",
    "register_in",
    "agent_registry",
    "register_agent",
    "llm_registry",
    "register_llm_provider",
    "discover_and_register",
]
```

- [ ] **Step 2: Verify syntax**

Run: `python3 -m py_compile app/core/registry/__init__.py`
Expected: No output (success)

- [ ] **Step 3: Commit**

```bash
git add app/core/registry/__init__.py
git commit -m "chore(registry): export discover_and_register utility"
```

---

## Task 8: Final Integration Test

**Files:**
- Modify: `tests/test_skills.py`

- [ ] **Step 1: Write integration test**

Add to `tests/test_skills.py`:
```python
class TestSkillIntegration:
    @pytest.mark.asyncio
    async def test_skill_standalone_execution(self):
        """Skill can run independently without Agent."""
        from app.skills.validation import ValidationSkill
        skill = ValidationSkill()
        result = await skill.execute({
            "content": "functional requirements\nacceptance criteria",
            "rules": ["functional", "acceptance"]
        })
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
                    result = await self.call_skill("prompt_enhance", {
                        "prompt": context.get("task", ""),
                        "context": {"language": "python"},
                    })
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
```

- [ ] **Step 2: Run all skill tests**

Run: `python3 -m pytest tests/test_skills.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_skills.py
git commit -m "test(skills): add integration tests for standalone and composed Skill usage"
```

---

## Task 9: Update Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add Skill system to project structure**

In README.md Project Structure section, add:
```
│   ├── skills/                   # Pluggable Skill system
│   │   ├── base.py              # BaseSkill, SkillResult, SkillConfig
│   │   ├── registry.py          # SkillRegistry with decorator registration
│   │   ├── code_search.py       # Code search skill
│   │   ├── prompt_enhance.py    # Prompt enhancement skill
│   │   └── validation.py        # Output validation skill
```

- [ ] **Step 2: Add Skill usage example**

In README.md, add after API Usage section:
```markdown
### Using Skills

Skills are independent, reusable capability units that can be used standalone or composed with Agents.

#### Standalone Usage

```python
from app.skills.code_search import CodeSearchSkill

skill = CodeSearchSkill()
result = await skill.execute({"query": "authentication", "repo_path": "./my-project"})
print(result.output)
```

#### Compose with Agent

```python
from app.agents.architect import ArchitectAgent
from app.skills.code_search import CodeSearchSkill

agent = ArchitectAgent(llm_router, state_repo)
agent.use_skill(CodeSearchSkill())

# Agent will automatically use code_search skill during proposal generation
proposal = await agent.generate_proposal(project_id, context)
```
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add Skill system to project structure and usage examples"
```

---

## Summary

This plan implements a pluggable Skill system with the following characteristics:

1. **Skills are independent** — Can be instantiated and executed without an Agent
2. **Skills are composable** — Agents can optionally `use_skill()` to enhance capabilities
3. **Registry pattern** — Global `SkillRegistry` with `@register_skill` decorator for discovery
4. **Backward compatible** — Existing Agents continue to work unchanged
5. **Demonstrated in ArchitectAgent** — Shows how an Agent can conditionally use a Skill
6. **Activities refactored** — Reuse LLMRouter and Agent instances, inject Skills where needed

All changes are incremental and do not break existing functionality.
