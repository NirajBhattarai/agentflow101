"""
Orchestrator Agent Definition

Defines the OrchestratorAgent class.
"""

from google.adk.agents import LlmAgent  # noqa: E402
from ag_ui_adk import ADKAgent  # noqa: E402

from .core.constants import (  # noqa: E402
    get_model_name,
    check_api_keys,
    DEFAULT_USER_ID,
    DEFAULT_APP_NAME,
    DEFAULT_SESSION_TIMEOUT,
    AGENT_NAME,
)
from .core.instruction import ORCHESTRATOR_INSTRUCTION  # noqa: E402


def build_orchestrator_agent() -> LlmAgent:
    """Build and configure the orchestrator LLM agent."""
    model_name = get_model_name()
    check_api_keys()
    return LlmAgent(
        name=AGENT_NAME,
        model=model_name,
        instruction=ORCHESTRATOR_INSTRUCTION,
    )


def build_adk_orchestrator_agent() -> ADKAgent:
    """Build ADK agent wrapper for AG-UI Protocol."""
    orchestrator_agent = build_orchestrator_agent()
    return ADKAgent(
        adk_agent=orchestrator_agent,
        app_name=DEFAULT_APP_NAME,
        user_id=DEFAULT_USER_ID,
        session_timeout_seconds=DEFAULT_SESSION_TIMEOUT,
        use_in_memory_services=True,
    )
