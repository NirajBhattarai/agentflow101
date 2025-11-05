"""
Bridge Agent Server (ADK + A2A Protocol)

Starts the Bridge Agent as an A2A Protocol server.
"""

import uvicorn
import os
from dotenv import load_dotenv
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from .bridge_executor import BridgeExecutor

load_dotenv()

port = int(os.getenv("BRIDGE_PORT", 9996))

skill = AgentSkill(
    id="bridge_agent",
    name="Token Bridge Agent",
    description="Handles token bridging across blockchain chains (Polygon, Hedera) using ADK",
    tags=["defi", "bridge", "blockchain", "multi-chain", "adk", "cross-chain"],
    examples=[
        "Bridge 100 USDC from Hedera to Polygon",
        "Bridge 50 HBAR from Hedera to Polygon",
        "Bridge 200 USDT from Polygon to Hedera",
        "Get bridge quote for 1000 USDC from Polygon to Hedera",
    ],
)

cardUrl = os.getenv("RENDER_EXTERNAL_URL", f"http://localhost:{port}")
public_agent_card = AgentCard(
    name="Bridge Agent",
    description="ADK-powered agent that handles token bridging across multiple blockchain chains",
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
        agent_executor=BridgeExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        extended_agent_card=public_agent_card,
    )

    print(f"🌉 Starting Bridge Agent (ADK + A2A) on http://0.0.0.0:{port}")
    print(f"   Agent: {public_agent_card.name}")
    print(f"   Description: {public_agent_card.description}")
    uvicorn.run(server.build(), host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

