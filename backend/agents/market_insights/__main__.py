"""
Market Insights Agent Server (ADK + A2A Protocol)

Starts the Market Insights Agent as an A2A Protocol server.
"""

import uvicorn
import os
from dotenv import load_dotenv
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from .executor import MarketInsightsExecutor

load_dotenv()

port = int(os.getenv("MARKET_INSIGHTS_PORT", 9992))

skill = AgentSkill(
    id="market_insights_agent",
    name="MarketInsightsAgent",
    description="Fetches liquidity across pools, volume, trending token addresses, and real-time prices using CoinGecko API",
    tags=[
        "defi",
        "market-insights",
        "liquidity",
        "volume",
        "trending",
        "price",
        "coingecko",
        "adk",
    ],
    examples=[
        "Get liquidity for WETH on Ethereum",
        "Show me trending tokens on Polygon",
        "Get price and volume for USDT on Hedera",
        "Find trending pools across all networks",
        "Get liquidity across all pools for ETH token",
    ],
)

cardUrl = os.getenv("RENDER_EXTERNAL_URL", f"http://localhost:{port}")
public_agent_card = AgentCard(
    name="MarketInsightsAgent",
    description="Fetches comprehensive market data: liquidity across pools, volume, trending tokens, and real-time prices using CoinGecko API",
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

    if not os.getenv("COINGECKO_API_KEY"):
        print("⚠️  Warning: CoinGecko API key not found!")
        print("   Set COINGECKO_API_KEY environment variable")
        print("   Example: export COINGECKO_API_KEY='your-key-here'")
        print("   Get a key from: https://www.coingecko.com/en/api/pricing")
        print()

    request_handler = DefaultRequestHandler(
        agent_executor=MarketInsightsExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=public_agent_card,
        http_handler=request_handler,
        extended_agent_card=public_agent_card,
    )

    print(
        f"📊 Starting Market Insights Agent (ADK + A2A) on http://0.0.0.0:{port}"
    )
    print(f"   Agent: {public_agent_card.name}")
    print(f"   Description: {public_agent_card.description}")
    uvicorn.run(server.build(), host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

