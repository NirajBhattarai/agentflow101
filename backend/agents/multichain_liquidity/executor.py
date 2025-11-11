"""
Multi-Chain Liquidity Agent Executor (A2A Protocol)

Handles A2A protocol requests for the Multi-Chain Liquidity Agent.
"""

import json
from dotenv import load_dotenv

load_dotenv()

# A2A Protocol imports
from a2a.server.agent_execution import AgentExecutor, RequestContext  # noqa: E402
from a2a.server.events import EventQueue  # noqa: E402
from a2a.utils import new_agent_text_message  # noqa: E402

from .core.constants import (
    DEFAULT_USER_ID,
    RESPONSE_TYPE,
    ERROR_CANCEL_NOT_SUPPORTED,
)
from .agent import MultiChainLiquidityAgent  # noqa: E402


def _get_session_id(context: RequestContext) -> str:
    """Extract session ID from context."""
    return getattr(context, "context_id", DEFAULT_USER_ID)


def _build_empty_response() -> str:
    """Build empty response fallback."""
    return json.dumps(
        {
            "type": RESPONSE_TYPE,
            "token_pair": None,
            "chain": None,
            "chains": {
                "hedera": {"pairs": [], "total_pools": 0},
                "polygon": {"pairs": [], "total_pools": 0},
                "ethereum": {"pairs": [], "total_pools": 0},
            },
            "hedera_pairs": [],
            "polygon_pairs": [],
            "ethereum_pairs": [],
            "all_pairs": [],
            "error": "Empty response from agent",
        },
        indent=2,
    )


def _build_execution_error_response(error: Exception) -> str:
    """Build response for execution error."""
    return json.dumps(
        {
            "type": RESPONSE_TYPE,
            "token_pair": None,
            "chain": None,
            "chains": {
                "hedera": {"pairs": [], "total_pools": 0},
                "polygon": {"pairs": [], "total_pools": 0},
                "ethereum": {"pairs": [], "total_pools": 0},
            },
            "hedera_pairs": [],
            "polygon_pairs": [],
            "ethereum_pairs": [],
            "all_pairs": [],
            "error": f"Execution error: {str(error)}",
        },
        indent=2,
    )


class MultiChainLiquidityExecutor(AgentExecutor):
    """Executor for Multi-Chain Liquidity Agent using A2A Protocol."""

    def __init__(self):
        self.agent = MultiChainLiquidityAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the multi-chain liquidity agent request."""
        query = context.get_user_input()
        session_id = _get_session_id(context)
        try:
            content = await self.agent.invoke(query, session_id)
            if not content or not content.strip():
                content = _build_empty_response()
            await event_queue.enqueue_event(new_agent_text_message(content))
            print("✅ Successfully enqueued multi-chain liquidity response")
        except Exception as e:
            print(f"❌ Error in execute: {e}")
            import traceback

            traceback.print_exc()
            error_response = _build_execution_error_response(e)
            await event_queue.enqueue_event(new_agent_text_message(error_response))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel execution (not supported)."""
        raise Exception(ERROR_CANCEL_NOT_SUPPORTED)
