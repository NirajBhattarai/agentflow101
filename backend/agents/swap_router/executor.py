"""
Swap Router Agent Executor (A2A Protocol)

Handles A2A protocol requests for the Swap Router Agent.
"""

import json
from dotenv import load_dotenv

load_dotenv()

# A2A Protocol imports
from a2a.server.agent_execution import AgentExecutor, RequestContext  # noqa: E402
from a2a.server.events import EventQueue  # noqa: E402
from a2a.utils import new_agent_text_message  # noqa: E402

from .core.constants import (  # noqa: E402
    DEFAULT_USER_ID,
    RESPONSE_TYPE,
    ERROR_CANCEL_NOT_SUPPORTED,
)
from .agent import SwapRouterAgent  # noqa: E402


def _get_session_id(context: RequestContext) -> str:
    """Extract session ID from context."""
    return getattr(context, "context_id", DEFAULT_USER_ID)


def _build_empty_response() -> str:
    """Build empty response fallback."""
    return json.dumps(
        {
            "type": RESPONSE_TYPE,
            "total_input": 0,
            "token_in": "unknown",
            "total_output": 0,
            "token_out": "unknown",
            "total_price_impact_percent": 0,
            "total_gas_cost_usd": 0,
            "net_output": 0,
            "efficiency_percent": 0,
            "routes": [],
            "recommendation_text": "Empty response from agent",
            "error": "Empty response from agent",
        },
        indent=2,
    )


def _build_execution_error_response(error: Exception) -> str:
    """Build response for execution error."""
    return json.dumps(
        {
            "type": RESPONSE_TYPE,
            "total_input": 0,
            "token_in": "unknown",
            "total_output": 0,
            "token_out": "unknown",
            "total_price_impact_percent": 0,
            "total_gas_cost_usd": 0,
            "net_output": 0,
            "efficiency_percent": 0,
            "routes": [],
            "recommendation_text": "",
            "error": f"Execution error: {str(error)}",
        },
        indent=2,
    )


class SwapRouterExecutor(AgentExecutor):
    """Executor for Swap Router Agent using A2A Protocol."""

    def __init__(self):
        self.agent = SwapRouterAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the swap router agent request."""
        query = context.get_user_input()
        session_id = _get_session_id(context)
        try:
            content = await self.agent.invoke(query, session_id)
            if not content or not content.strip():
                content = _build_empty_response()
            await event_queue.enqueue_event(new_agent_text_message(content))
            print("✅ Successfully enqueued swap router response")
        except Exception as e:
            print(f"❌ Error in execute: {e}")
            import traceback

            traceback.print_exc()
            error_response = _build_execution_error_response(e)
            await event_queue.enqueue_event(new_agent_text_message(error_response))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel execution (not supported)."""
        raise Exception(ERROR_CANCEL_NOT_SUPPORTED)

