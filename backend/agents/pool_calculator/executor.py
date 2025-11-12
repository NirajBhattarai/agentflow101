"""
Pool Calculator Agent Executor (A2A Protocol)

Handles A2A protocol requests for the Pool Calculator Agent.
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
from .agent import PoolCalculatorAgent  # noqa: E402


def _get_session_id(context: RequestContext) -> str:
    """Extract session ID from context."""
    return getattr(context, "context_id", DEFAULT_USER_ID)


def _build_empty_response() -> str:
    """Build empty response fallback."""
    return json.dumps(
        {
            "type": RESPONSE_TYPE,
            "response": "No response generated",
        }
    )


def _build_execution_error_response(error: Exception) -> str:
    """Build error response."""
    return json.dumps(
        {
            "type": "error",
            "error": str(error),
            "message": f"Pool Calculator Agent error: {error}",
        }
    )


class PoolCalculatorExecutor(AgentExecutor):
    """Executor for Pool Calculator Agent using A2A Protocol."""

    def __init__(self):
        self.agent = PoolCalculatorAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the pool calculator agent request."""
        query = context.get_user_input()
        session_id = _get_session_id(context)
        try:
            content = await self.agent.invoke(query, session_id)

            # Ensure content is always valid JSON
            if not content or not content.strip():
                content = _build_empty_response()
            else:
                # Validate that content is valid JSON
                try:
                    json.loads(content)
                except json.JSONDecodeError:
                    # If not valid JSON, wrap it in a valid JSON structure
                    print("⚠️  Pool Calculator response is not valid JSON, wrapping it")
                    content = json.dumps(
                        {
                            "recommended_allocations": {},
                            "total_output": 0.0,
                            "average_price_impact": 0.0,
                            "reasoning": f"Invalid JSON response: {content[:200]}",
                            "error": "Response is not valid JSON",
                        }
                    )

            await event_queue.enqueue_event(new_agent_text_message(content))
            print(
                f"✅ Successfully enqueued pool calculator response ({len(content)} chars)"
            )
        except Exception as e:
            print(f"❌ Error in execute: {e}")
            import traceback

            traceback.print_exc()
            error_response = _build_execution_error_response(e)
            await event_queue.enqueue_event(new_agent_text_message(error_response))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel execution (not supported)."""
        raise Exception(ERROR_CANCEL_NOT_SUPPORTED)
