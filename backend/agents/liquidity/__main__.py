import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from .liquidity_executor import LiquidityExecutor


def main():
    """Starts the Liquidity Agent server."""

    liquidity_agent_skill = AgentSkill(
        id="get_liquidity",
        name="Get Liquidity from Multiple Chains",
        description="Retrieve liquidity information from different blockchain chains including Ethereum, BSC, Polygon, and Hedera",
        examples=[
            "Get liquidity for USDC token on Ethereum",
            "Find all liquidity pools for HBAR on Hedera",
            "Compare liquidity across all chains for a token",
            "Get liquidity information from Polygon",
        ],
        input_modes=[
            "text",
        ],
        output_modes=[
            "text",
        ],
        security=[
            {
                "tags": ["defi", "liquidity", "blockchain"],
            }
        ],
        tags=["defi", "liquidity", "multi-chain"],
    )

    liquidity_agent_card = AgentCard(
        id="liquidity_agent",
        name="Liquidity Agent",
        description="Retrieves liquidity information from multiple blockchain chains (Ethereum, BSC, Polygon, Hedera)",
        skills=[liquidity_agent_skill],
        url="http://localhost:9998/",
        version="0.1.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
    )

    request_handler = DefaultRequestHandler(
        agent_executor=LiquidityExecutor(),
        task_store=InMemoryTaskStore(),
    )
    liquidity_server = A2AStarletteApplication(
        agent_card=liquidity_agent_card,
        http_handler=request_handler,
        extended_agent_card=liquidity_agent_card,
    )

    uvicorn.run(liquidity_server.build(), host="0.0.0.0", port=9998)


if __name__ == "__main__":
    main()
