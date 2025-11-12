"""
Pool Calculator Agent Server (ADK + A2A Protocol)

Starts the Pool Calculator Agent as an A2A Protocol server.
"""

import uvicorn
import os
from dotenv import load_dotenv
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from .executor import PoolCalculatorExecutor
from .core.constants import AGENT_NAME, AGENT_DESCRIPTION

load_dotenv()

port = int(os.getenv("POOL_CALCULATOR_PORT", 9996))

skill = AgentSkill(
    id="pool_calculator_agent",
    name=AGENT_NAME,
    description=AGENT_DESCRIPTION,
    tags=["defi", "pool", "calculation", "liquidity", "slot0", "adk"],
    examples=[
        "Calculate price from sqrtPriceX96 for USDT/WETH pool",
        "What's the swap output for 1000 USDT in this pool?",
        "Analyze the health of this liquidity pool",
        "Recommend optimal swap allocation for 1M USDT to ETH",
    ],
)

cardUrl = os.getenv("RENDER_EXTERNAL_URL", f"http://localhost:{port}")
public_agent_card = AgentCard(
    name=AGENT_NAME,
    description=AGENT_DESCRIPTION,
    url=cardUrl,
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(
        text=True,
        image=False,
        audio=False,
        video=False,
        function_calling=True,
    ),
    skills=[skill],
    supportsAuthenticatedExtendedCard=False,
)


def main():
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: No API key found!")
        print("   Set either GOOGLE_API_KEY or GEMINI_API_KEY environment variable")
        print("   Example: export GOOGLE_API_KEY='your-key-here'")
        print("   Get a key from: https://aistudio.google.com/app/apikey")
        print()

    request_handler = DefaultRequestHandler(
        agent_executor=PoolCalculatorExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        extended_agent_card=public_agent_card,
    )

    print(f"🧮 Starting Pool Calculator Agent (ADK + A2A) on http://0.0.0.0:{port}")
    print(f"   Agent: {public_agent_card.name}")
    print(f"   Description: {public_agent_card.description}")
    uvicorn.run(server.build(), host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
