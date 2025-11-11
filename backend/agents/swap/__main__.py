"""
Swap Agent Server (ADK + A2A Protocol)

Starts the Swap Agent as an A2A Protocol server.
"""

import uvicorn
import os
from dotenv import load_dotenv
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from .executor import SwapExecutor

load_dotenv()

port = int(os.getenv("SWAP_PORT", 9995))

skill = AgentSkill(
    id="swap_agent",
    name="Token Swap Agent",
    description="Handles token swaps on blockchain chains (Polygon, Hedera) using ADK. TEMPORARY: Direct swap without quotes.",
    tags=["defi", "swap", "blockchain", "multi-chain", "adk", "dex"],
    examples=[
        "Swap 0.01 HBAR to USDC on Hedera",
        "Swap 100 USDC to HBAR on Hedera",
        "Swap 50 MATIC to USDC on Polygon",
        "Swap 0.1 HBAR to USDC on Hedera for account 0.0.123456",
    ],
)

cardUrl = os.getenv("RENDER_EXTERNAL_URL", f"http://localhost:{port}")
public_agent_card = AgentCard(
    name="Swap Agent",
    description="ADK-powered agent that handles token swaps on multiple blockchain chains. TEMPORARY: Direct swap execution.",
    url=cardUrl,
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=True),
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
        agent_executor=SwapExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        extended_agent_card=public_agent_card,
    )

    print(f"💱 Starting Swap Agent (ADK + A2A) on http://0.0.0.0:{port}")
    print(f"   Agent: {public_agent_card.name}")
    print(f"   Description: {public_agent_card.description}")
    print("   ⚠️  TEMPORARY: Direct swap mode (no quotes)")
    uvicorn.run(server.build(), host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
