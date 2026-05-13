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


async def analyze_requirement(context: ActivityContext) -> Dict[str, Any]:
    """Business Analyst activity: analyze user requirements."""
    requirement = context.inputs.get("requirement", "")
    if not requirement:
        raise ValueError("No requirement provided")

    router = LLMRouter()
    agent = BusinessAnalystAgent(
        llm_router=router,
        state_repository=_get_state_repo(),
    )

    proposal = await agent.generate_proposal(
        project_id=context.project_id,
        context={"requirement": requirement},
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
    """Product Manager activity: generate PRD from analysis."""
    analysis = context.inputs.get("previous_output", {}).get("analysis", "")
    if not analysis:
        raise ValueError("No analysis provided")

    router = LLMRouter()
    agent = ProductManagerAgent(
        llm_router=router,
        state_repository=_get_state_repo(),
    )

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
    """Architect activity: analyze code impact and propose design."""
    prd = context.inputs.get("previous_output", {}).get("prd", "")
    if not prd:
        raise ValueError("No PRD provided")

    router = LLMRouter()
    agent = ArchitectAgent(
        llm_router=router,
        state_repository=_get_state_repo(),
    )

    proposal = await agent.generate_proposal(
        project_id=context.project_id,
        context={"prd": prd},
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
    """Developer activity: generate code patch."""
    architecture = context.inputs.get("previous_output", {}).get("architecture", "")
    if not architecture:
        raise ValueError("No architecture provided")

    router = LLMRouter()
    agent = DeveloperAgent(
        llm_router=router,
        state_repository=_get_state_repo(),
    )

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
    """QA activity: generate test plan and test cases."""
    patch = context.inputs.get("previous_output", {}).get("patch", "")
    if not patch:
        raise ValueError("No patch provided")

    router = LLMRouter()
    agent = QAAgent(
        llm_router=router,
        state_repository=_get_state_repo(),
    )

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
    """QA activity: execute generated tests."""
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


def _get_state_repo() -> StateRepository:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.config import get_settings
    from app.state.models import Base

    settings = get_settings()
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    return StateRepository(db)


ACTIVITY_MAP = {
    "analyze_requirement": analyze_requirement,
    "generate_prd": generate_prd,
    "analyze_code_impact": analyze_code_impact,
    "generate_patch": generate_patch,
    "generate_tests": generate_tests,
    "execute_tests": execute_tests,
}
