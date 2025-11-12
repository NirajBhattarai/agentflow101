"""
Market Insights Agent Executor (A2A Protocol)

Handles A2A protocol requests for the Market Insights Agent.
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
from .agent import MarketInsightsAgent  # noqa: E402


def _get_session_id(context: RequestContext) -> str:
    """Extract session ID from context."""
    return getattr(context, "context_id", DEFAULT_USER_ID)


def _build_empty_response() -> str:
    """Build empty response fallback."""
    return json.dumps(
        {
            "type": RESPONSE_TYPE,
            "error": "Empty response from agent",
        },
        indent=2,
    )


def _build_execution_error_response(error: Exception) -> str:
    """Build response for execution error."""
    return json.dumps(
        {
            "type": RESPONSE_TYPE,
            "error": f"Execution error: {str(error)}",
        },
        indent=2,
    )


class MarketInsightsExecutor(AgentExecutor):
    """Executor for Market Insights Agent using A2A Protocol."""

    def __init__(self):
        self.agent = MarketInsightsAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the market insights agent request."""
        query = context.get_user_input()
        session_id = _get_session_id(context)
        try:
            content = await self.agent.invoke(query, session_id)
            if not content or not content.strip():
                content = _build_empty_response()

            # Validate JSON before enqueuing
            try:
                json.loads(content)
            except json.JSONDecodeError:
                # If not valid JSON, wrap it
                content = json.dumps(
                    {
                        "type": RESPONSE_TYPE,
                        "error": "Invalid JSON response from agent",
                        "raw_response": content[:500],  # Limit length
                    },
                    indent=2,
                )

            await event_queue.enqueue_event(new_agent_text_message(content))
            print("✅ Successfully enqueued market insights response")
        except Exception as e:
            print(f"❌ Error in execute: {e}")
            import traceback

            traceback.print_exc()
            error_response = _build_execution_error_response(e)
            await event_queue.enqueue_event(new_agent_text_message(error_response))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel execution (not supported)."""
        raise Exception(ERROR_CANCEL_NOT_SUPPORTED)
