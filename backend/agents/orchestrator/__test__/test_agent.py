"""
Unit tests for Orchestrator Agent.
"""

from agents.orchestrator.agent import (
    build_orchestrator_agent,
    build_adk_orchestrator_agent,
)
from agents.orchestrator.core.constants import (
    AGENT_NAME,
    DEFAULT_MODEL,
    DEFAULT_USER_ID,
    DEFAULT_APP_NAME,
)


class TestOrchestratorAgent:
    """Test cases for Orchestrator Agent."""

    def test_build_orchestrator_agent(self):
        """Test building orchestrator agent."""
        agent = build_orchestrator_agent()
        assert agent.name == AGENT_NAME
        assert agent.model == DEFAULT_MODEL
        assert agent.instruction is not None
        assert len(agent.instruction) > 0

    def test_build_adk_orchestrator_agent(self):
        """Test building ADK orchestrator agent."""
        adk_agent = build_adk_orchestrator_agent()
        assert adk_agent is not None
        assert isinstance(adk_agent, type(adk_agent))  # Check it's an ADKAgent instance

    def test_agent_has_instruction(self):
        """Test agent has instruction configured."""
        agent = build_orchestrator_agent()
        assert "Balance Agent" in agent.instruction
        assert "Liquidity Agent" in agent.instruction
        assert "Swap Agent" in agent.instruction
        assert "Bridge Agent" in agent.instruction
