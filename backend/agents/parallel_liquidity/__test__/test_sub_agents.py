"""
Unit tests for parallel liquidity sub-agents.
"""

from agents.parallel_liquidity.agents.hedera_liquidity_agent import (
    build_hedera_liquidity_agent,
)
from agents.parallel_liquidity.agents.polygon_liquidity_agent import (
    build_polygon_liquidity_agent,
)


class TestHederaLiquidityAgent:
    """Test cases for Hedera liquidity sub-agent."""

    def test_build_hedera_liquidity_agent(self):
        """Test building Hedera liquidity agent."""
        agent = build_hedera_liquidity_agent()
        assert agent is not None
        assert agent.name == "HederaLiquidityAgent"
        assert agent.model is not None
        assert len(agent.instruction) > 0
        assert "Hedera" in agent.instruction
        assert "SaucerSwap" in agent.instruction

    def test_hedera_agent_has_tools(self):
        """Test that Hedera agent has required tools."""
        agent = build_hedera_liquidity_agent()
        assert agent.tools is not None
        assert len(agent.tools) > 0

    def test_hedera_agent_output_key(self):
        """Test that Hedera agent has correct output key."""
        agent = build_hedera_liquidity_agent()
        assert hasattr(agent, "output_key")
        assert agent.output_key == "hedera_liquidity"


class TestPolygonLiquidityAgent:
    """Test cases for Polygon liquidity sub-agent."""

    def test_build_polygon_liquidity_agent(self):
        """Test building Polygon liquidity agent."""
        agent = build_polygon_liquidity_agent()
        assert agent is not None
        assert agent.name == "PolygonLiquidityAgent"
        assert agent.model is not None
        assert len(agent.instruction) > 0
        assert "Polygon" in agent.instruction

    def test_polygon_agent_has_tools(self):
        """Test that Polygon agent has required tools."""
        agent = build_polygon_liquidity_agent()
        assert agent.tools is not None
        assert len(agent.tools) > 0

    def test_polygon_agent_output_key(self):
        """Test that Polygon agent has correct output key."""
        agent = build_polygon_liquidity_agent()
        assert hasattr(agent, "output_key")
        assert agent.output_key == "polygon_liquidity"
