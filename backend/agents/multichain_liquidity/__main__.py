"""
Multi-Chain Liquidity Agent Server (ADK + A2A Protocol)

Starts the Multi-Chain Liquidity Agent as an A2A Protocol server.
"""

import uvicorn
import os
from dotenv import load_dotenv
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from .executor import MultiChainLiquidityExecutor

load_dotenv()

port = int(os.getenv("MULTICHAIN_LIQUIDITY_PORT", 9994))

skill = AgentSkill(
    id="multichain_liquidity_agent",
    name="MultiChainLiquidityAgent",
    description="Fetches liquidity information sequentially from Hedera, Polygon, and Ethereum chains",
    tags=["defi", "liquidity", "multi-chain", "hedera", "polygon", "ethereum", "adk"],
    examples=[
        "Get liquidity for ETH/USDT",
        "Get liquidity for HBAR/USDC on all chains",
        "Show me liquidity pools on Polygon",
        "Get liquidity from Ethereum for USDT",
    ],
)

cardUrl = os.getenv("RENDER_EXTERNAL_URL", f"http://localhost:{port}")
public_agent_card = AgentCard(
    name="MultiChainLiquidityAgent",
    description="Unified agent that fetches liquidity sequentially from Hedera, Polygon, and Ethereum chains",
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
        agent_executor=MultiChainLiquidityExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        extended_agent_card=public_agent_card,
    )

    print(
        f"💧 Starting Multi-Chain Liquidity Agent (ADK + A2A) on http://0.0.0.0:{port}"
    )
    print(f"   Agent: {public_agent_card.name}")
    print(f"   Description: {public_agent_card.description}")
    uvicorn.run(server.build(), host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
