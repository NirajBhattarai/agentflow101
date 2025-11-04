from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
import os

from google.genai import types

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from .tools import (
    get_liquidity_ethereum,
    get_liquidity_bsc,
    get_liquidity_polygon,
    get_liquidity_hedera,
    get_liquidity_all_chains,
    log_message,
)


# Initialize model
nebius_model = LiteLlm(
    model="openai/meta-llama/Meta-Llama-3.1-8B-Instruct",
    api_base=os.getenv("NEBIUS_API_BASE"),
    api_key=os.getenv("NEBIUS_API_KEY"),
)

# Create liquidity agent
liquidity_agent = Agent(
    name="LiquidityAgent",
    model=nebius_model,
    description="Fetches liquidity information from different blockchain chains including Ethereum, BSC, Polygon, and Hedera.",
    instruction="Use the available tools to retrieve liquidity information for tokens across different chains. You can query specific chains or get liquidity from all chains. Provide comprehensive liquidity data including pool addresses, DEX names, TVL, and 24h volume.",
    tools=[
        get_liquidity_ethereum,
        get_liquidity_bsc,
        get_liquidity_polygon,
        get_liquidity_hedera,
        get_liquidity_all_chains,
        log_message,
    ],
    output_key="liquidity_data",
)

# Initialize session and runner
session_service = InMemorySessionService()
runner = Runner(
    agent=liquidity_agent, app_name="liquidity_app", session_service=session_service
)


class LiquidityAgent:
    """Liquidity Agent."""

    async def invoke(self) -> str:
        return "Liquidity Agent is running"


class LiquidityExecutor(AgentExecutor):
    """Liquidity Agent Executor Implementation."""

    def __init__(self):
        self.agent = liquidity_agent

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        # Create a session
        session = await session_service.create_session(
            app_name="liquidity_app", user_id="user_1"
        )

        # Extract user message from context
        user_message_text = "Get liquidity information"
        if context.request and hasattr(context.request, "message"):
            if (
                hasattr(context.request.message, "parts")
                and context.request.message.parts
            ):
                user_message_text = context.request.message.parts[0].text
            elif (
                isinstance(context.request.message, dict)
                and "parts" in context.request.message
            ):
                user_message_text = context.request.message["parts"][0].get(
                    "text", "Get liquidity information"
                )

        # Create a user message
        user_message = types.Content(
            role="user", parts=[types.Part(text=user_message_text)]
        )

        # Run the agent using Runner
        async for event in runner.run_async(
            user_id="user_1", session_id=session.id, new_message=user_message
        ):
            if event.is_final_response():
                # Extract the response text
                response_text = event.content.parts[0].text
                # Enqueue the response as an A2A event
                await event_queue.enqueue_event(new_agent_text_message(response_text))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")
