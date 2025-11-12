"""
Bridge Executor (A2A Protocol)

Handles execution of bridge agent requests through A2A Protocol.
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
    ERROR_CANCEL_NOT_SUPPORTED,
    RESPONSE_TYPE,
    CHAIN_UNKNOWN,
)
from .agent import BridgeAgent  # noqa: E402
from .services.response_validator import (  # noqa: E402
    validate_response_content,
    log_sending_response,
    build_execution_error_response,
)


def _get_session_id(context: RequestContext) -> str:
    """Extract session ID from context."""
    return getattr(context, "context_id", DEFAULT_SESSION_ID)


def _build_empty_response() -> str:
    """Build empty response fallback."""
    return json.dumps(
        {
            "type": RESPONSE_TYPE,
            "source_chain": CHAIN_UNKNOWN,
            "destination_chain": CHAIN_UNKNOWN,
            "token_symbol": "unknown",
            "amount": "0",
            "error": "Empty response from agent",
        },
        indent=2,
    )


class BridgeExecutor(AgentExecutor):
    def __init__(self):
        self.agent = BridgeAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the bridge agent request."""
        query = context.get_user_input()
        session_id = _get_session_id(context)
        try:
            content = await self.agent.invoke(query, session_id)
            if not content or not content.strip():
                content = _build_empty_response()
            validated_content = validate_response_content(content)
            log_sending_response(validated_content)
            await event_queue.enqueue_event(new_agent_text_message(validated_content))
            print("✅ Successfully enqueued response")
        except Exception as e:
            print(f"❌ Error in execute: {e}")
            import traceback

            traceback.print_exc()
            error_response = build_execution_error_response(e)
            await event_queue.enqueue_event(new_agent_text_message(error_response))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel execution (not supported)."""
        raise Exception(ERROR_CANCEL_NOT_SUPPORTED)

