"""
Integration tests for Parallel Liquidity Agent.

Tests the full flow from executor -> agent -> sub-agents -> tools.
"""

import json
import pytest
from typing import List

from agents.parallel_liquidity.agent import ParallelLiquidityAgent
from agents.parallel_liquidity.executor import ParallelLiquidityExecutor


class MockRequestContext:
    """Mock RequestContext for testing."""

    def __init__(self, user_input: str, context_id: str = "test-session-123"):
        self._user_input = user_input
        self.context_id = context_id

    def get_user_input(self) -> str:
        """Get user input."""
        return self._user_input


class MockEventQueue:
    """Mock EventQueue for testing."""

    def __init__(self):
        self.events: List[dict] = []

    async def enqueue_event(self, event: dict):
        """Enqueue an event."""
        self.events.append(event)

    def get_last_event(self) -> dict:
        """Get the last enqueued event."""
        return self.events[-1] if self.events else None

    def clear(self):
        """Clear all events."""
        self.events = []


class TestParallelLiquidityAgentIntegration:
    """Integration tests for ParallelLiquidityAgent."""

    @pytest.mark.asyncio
    async def test_agent_token_pair_extraction(self):
        """Test agent correctly extracts token pair from query."""
        from agents.parallel_liquidity.services.query_parser import extract_token_pair

        query = "Get liquidity for HBAR/USDC"
        token_pair = extract_token_pair(query)
        assert token_pair == "HBAR/USDC"

    @pytest.mark.asyncio
    async def test_agent_no_token_pair_error(self):
        """Test agent returns error when no token pair found."""
        agent = ParallelLiquidityAgent()
        query = "Get liquidity information"
        response = await agent.invoke(query, session_id="test")
        data = json.loads(response)

        assert data["type"] == "parallel_liquidity"
        assert "error" in data
        assert data["token_pair"] == ""
        assert len(data["hedera_pairs"]) == 0
        assert len(data["polygon_pairs"]) == 0

    @pytest.mark.asyncio
    async def test_agent_response_structure(self, test_token_pairs):
        """Test agent response has correct structure."""
        agent = ParallelLiquidityAgent()
        query = f"Get liquidity for {test_token_pairs[0]}"
        response = await agent.invoke(query, session_id="test")
        data = json.loads(response)

        assert "type" in data
        assert "token_pair" in data
        assert "chains" in data
        assert "hedera_pairs" in data
        assert "polygon_pairs" in data
        assert "all_pairs" in data
        assert data["type"] == "parallel_liquidity"

    @pytest.mark.asyncio
    async def test_agent_combines_results(
        self, mock_hedera_liquidity_result, mock_polygon_liquidity_result
    ):
        """Test agent correctly combines results from both chains."""
        from agents.parallel_liquidity.services.result_combiner import combine_results

        token_pair = "ETH/USDT"
        data = combine_results(
            token_pair, mock_hedera_liquidity_result, mock_polygon_liquidity_result
        )

        assert data["chains"]["hedera"]["total_pools"] > 0
        assert data["chains"]["polygon"]["total_pools"] > 0
        assert len(data["all_pairs"]) == (
            len(data["hedera_pairs"]) + len(data["polygon_pairs"])
        )


class TestParallelLiquidityExecutorIntegration:
    """Integration tests for ParallelLiquidityExecutor (A2A Protocol)."""

    @pytest.mark.asyncio
    async def test_executor_successful_execution(self, test_token_pairs):
        """Test executor successfully processes a liquidity request."""
        executor = ParallelLiquidityExecutor()
        context = MockRequestContext(
            user_input=f"Get liquidity for {test_token_pairs[0]}",
            context_id="test-executor-123",
        )
        event_queue = MockEventQueue()

        await executor.execute(context, event_queue)

        assert len(event_queue.events) > 0
        last_event = event_queue.get_last_event()
        assert last_event is not None

    @pytest.mark.asyncio
    async def test_executor_error_handling(self):
        """Test executor handles errors gracefully."""
        executor = ParallelLiquidityExecutor()
        context = MockRequestContext(user_input="Invalid query without token pair")
        event_queue = MockEventQueue()

        await executor.execute(context, event_queue)

        assert len(event_queue.events) > 0
        last_event = event_queue.get_last_event()
        assert last_event is not None

    @pytest.mark.asyncio
    async def test_executor_cancel_not_supported(self):
        """Test executor cancel method raises appropriate error."""
        executor = ParallelLiquidityExecutor()
        context = MockRequestContext(user_input="test")
        event_queue = MockEventQueue()

        with pytest.raises(Exception) as exc_info:
            await executor.cancel(context, event_queue)

        assert (
            "not supported" in str(exc_info.value).lower()
            or "cancel" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_executor_response_validation(self, test_token_pairs):
        """Test executor validates JSON response."""
        executor = ParallelLiquidityExecutor()
        context = MockRequestContext(
            user_input=f"Get liquidity for {test_token_pairs[0]}"
        )
        event_queue = MockEventQueue()

        await executor.execute(context, event_queue)

        assert len(event_queue.events) > 0
        last_event = event_queue.get_last_event()
        assert last_event is not None

        # Verify response is valid JSON
        if "text" in last_event:
            try:
                json.loads(last_event["text"])
            except json.JSONDecodeError:
                pytest.fail("Response is not valid JSON")


class TestEndToEndParallelLiquidityIntegration:
    """End-to-end integration tests covering full parallel liquidity flow."""

    @pytest.mark.asyncio
    async def test_full_flow_with_token_pair(self, test_token_pairs):
        """Test complete flow: Executor -> Agent -> Sub-agents -> Tools."""
        executor = ParallelLiquidityExecutor()
        context = MockRequestContext(
            user_input=f"Get liquidity for {test_token_pairs[0]}",
        )
        event_queue = MockEventQueue()

        await executor.execute(context, event_queue)

        assert len(event_queue.events) > 0

        agent = ParallelLiquidityAgent()
        response = await agent.invoke(
            context.get_user_input(), session_id=context.context_id
        )
        data = json.loads(response)

        assert data["type"] == "parallel_liquidity"
        assert data["token_pair"] == test_token_pairs[0]
        assert "chains" in data
        assert "hedera_pairs" in data
        assert "polygon_pairs" in data

    @pytest.mark.asyncio
    async def test_full_flow_multiple_pairs(self, test_token_pairs):
        """Test full flow with multiple different token pairs."""
        executor = ParallelLiquidityExecutor()

        for token_pair in test_token_pairs[:2]:  # Test first 2 pairs
            context = MockRequestContext(user_input=f"Get liquidity for {token_pair}")
            event_queue = MockEventQueue()

            await executor.execute(context, event_queue)

            assert len(event_queue.events) > 0

            agent = ParallelLiquidityAgent()
            response = await agent.invoke(
                context.get_user_input(), session_id=context.context_id
            )
            data = json.loads(response)

            assert data["type"] == "parallel_liquidity"
            assert data["token_pair"] == token_pair
