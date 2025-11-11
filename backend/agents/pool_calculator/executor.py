"""
A2A Protocol Executor for Pool Calculator Agent.
"""

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.event_queue import EventQueue
from .agent import PoolCalculatorAgent
from .core.constants import DEFAULT_SESSION_ID


class PoolCalculatorExecutor(AgentExecutor):
    """A2A executor for Pool Calculator Agent."""

    def __init__(self):
        self.agent = PoolCalculatorAgent()

    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """
        Execute A2A protocol request.

        Args:
            context: Request context with message
            event_queue: Event queue for responses
        """
        try:
            # Get message from context
            message = context.message
            if isinstance(message, dict):
                query = message.get("text", "") or message.get("query", "") or str(message)
            else:
                query = str(message)

            if not query:
                await event_queue.enqueue(
                    {
                        "type": "error",
                        "error": "No query provided",
                    }
                )
                return

            # Invoke agent
            session_id = context.session_id or DEFAULT_SESSION_ID
            response = await self.agent.invoke(query, session_id)

            # Enqueue response
            await event_queue.enqueue(
                {
                    "type": "pool_calculation",
                    "response": response,
                    "query": query,
                }
            )

        except Exception as e:
            error_msg = f"Error executing pool calculator: {e}"
            print(f"❌ {error_msg}")
            await event_queue.enqueue(
                {
                    "type": "error",
                    "error": error_msg,
                }
            )

