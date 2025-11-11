"""
Parallel Liquidity Agent Server (ADK + A2A Protocol)

Starts the Parallel Liquidity Agent as an A2A Protocol server.
This is a completely independent agent that fetches liquidity from
Hedera and Polygon chains in parallel.

Run with: uv run -m agents.parallel_liquidity
"""

import uvicorn
import os
from dotenv import load_dotenv
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from .executor import ParallelLiquidityExecutor

load_dotenv()

port = int(os.getenv("PARALLEL_LIQUIDITY_PORT", 9994))

skill = AgentSkill(
    id="parallel_liquidity_agent",
    name="Parallel Liquidity Query Agent",
    description="Retrieves liquidity information from multiple blockchain chains (Hedera, Polygon) in parallel using ParallelAgent",
    tags=["defi", "liquidity", "blockchain", "multi-chain", "adk", "parallel"],
    examples=[
        "Get liquidity for ETH/USDT",
        "Find liquidity pools for HBAR/USDC on Hedera and Polygon",
        "Get liquidity for USDC/USDT across all chains",
        "Show me liquidity for MATIC/USDC",
    ],
)

cardUrl = os.getenv("RENDER_EXTERNAL_URL", f"http://localhost:{port}")
public_agent_card = AgentCard(
    name="Parallel Liquidity Agent",
    description="Independent ADK-powered agent that retrieves liquidity from Hedera and Polygon chains in parallel",
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
        agent_executor=ParallelLiquidityExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        extended_agent_card=public_agent_card,
    )

    print(
        f"💧🚀 Starting Parallel Liquidity Agent (ADK + A2A) on http://0.0.0.0:{port}"
    )
    print(f"   Agent: {public_agent_card.name}")
    print(f"   Description: {public_agent_card.description}")
    print(f"   Port: {port}")
    print("   Features: Parallel execution for Hedera and Polygon chains")
    print("   Usage: Query with token pairs like 'ETH/USDT' or 'HBAR/USDC'")
    uvicorn.run(server.build(), host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
