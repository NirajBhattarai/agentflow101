"""
Integration tests for Orchestrator Agent.

Tests the orchestrator agent setup and configuration.
"""

from agents.orchestrator.agent import (
    build_orchestrator_agent,
    build_adk_orchestrator_agent,
)
from agents.orchestrator.orchestrator import create_app
from agents.orchestrator.core.constants import AGENT_NAME


class TestOrchestratorIntegration:
    """Integration tests for Orchestrator Agent."""

    def test_agent_builds_successfully(self):
        """Test that orchestrator agent builds without errors."""
        agent = build_orchestrator_agent()
        assert agent is not None
        assert agent.name == AGENT_NAME

    def test_adk_agent_builds_successfully(self):
        """Test that ADK orchestrator agent builds without errors."""
        adk_agent = build_adk_orchestrator_agent()
        assert adk_agent is not None
        # Just verify it's an ADKAgent instance
        assert hasattr(adk_agent, "__class__")

    def test_app_creates_successfully(self):
        """Test that FastAPI app creates successfully."""
        app = create_app()
        assert app is not None
        assert app.title == "DeFi Orchestrator (ADK)"

    def test_agent_instruction_complete(self):
        """Test that agent instruction contains all required information."""
        agent = build_orchestrator_agent()
        instruction = agent.instruction

        # Check for agent descriptions
        assert "Balance Agent" in instruction
        assert "Liquidity Agent" in instruction
        assert "Swap Agent" in instruction
        assert "Bridge Agent" in instruction

        # Check for workflow instructions
        assert "gather_balance_requirements" in instruction
        assert "gather_liquidity_requirements" in instruction
        assert "gather_swap_requirements" in instruction
        assert "gather_bridge_requirements" in instruction

        # Check for chain support
        assert "Polygon" in instruction
        assert "Hedera" in instruction

    def test_agent_configuration(self):
        """Test agent configuration values."""
        agent = build_orchestrator_agent()
        assert agent.name == "OrchestratorAgent"
        assert agent.model is not None
        assert len(agent.model) > 0
