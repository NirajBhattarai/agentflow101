"""
Parallel Liquidity Executor (A2A Protocol)

Thin adapter layer for A2A Protocol integration.
"""

import json
from dotenv import load_dotenv

load_dotenv()

# A2A Protocol imports
from a2a.server.agent_execution import AgentExecutor, RequestContext  # noqa: E402
from a2a.server.events import EventQueue  # noqa: E402
from a2a.utils import new_agent_text_message  # noqa: E402

from .core.constants import (  # noqa: E402
    DEFAULT_SESSION_ID,
    ERROR_EXECUTION_ERROR,
    ERROR_CANCEL_NOT_SUPPORTED,
    RESPONSE_TYPE,
)
from .agent import ParallelLiquidityAgent  # noqa: E402
from .services.response_validator import (  # noqa: E402
    validate_response_content,
    log_sending_response,
)


def _get_session_id(context: RequestContext) -> str:
    """Extract session ID from context."""
    return getattr(context, "context_id", DEFAULT_SESSION_ID)


def _build_execution_error_response(error: Exception) -> str:
    """Build response for execution error."""
    return json.dumps(
        {
            "type": RESPONSE_TYPE,
            "token_pair": "",
            "chains": {},
            "hedera_pairs": [],
            "polygon_pairs": [],
            "all_pairs": [],
            "error": f"{ERROR_EXECUTION_ERROR}: {str(error)}",
        },
        indent=2,
    )


class ParallelLiquidityExecutor(AgentExecutor):
    """A2A Protocol executor for parallel liquidity agent."""

    def __init__(self):
        self.agent = ParallelLiquidityAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the parallel liquidity agent request."""
        query = context.get_user_input()
        session_id = _get_session_id(context)
        try:
            content = await self.agent.invoke(query, session_id)
            validated_content = validate_response_content(content)
            log_sending_response(validated_content)
            await event_queue.enqueue_event(new_agent_text_message(validated_content))
            print("✅ Successfully enqueued response")
        except Exception as e:
            print(f"❌ Error in execute: {e}")
            import traceback

            traceback.print_exc()
            error_response = _build_execution_error_response(e)
            await event_queue.enqueue_event(new_agent_text_message(error_response))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel execution (not supported)."""
        raise Exception(ERROR_CANCEL_NOT_SUPPORTED)
