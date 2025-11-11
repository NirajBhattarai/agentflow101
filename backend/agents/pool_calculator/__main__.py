"""
Server entry point for Pool Calculator Agent.
"""

import uvicorn
from a2a.server import create_a2a_server
from a2a.server.agent_card import AgentCard
from a2a.server.agent_skill import AgentSkill
from .executor import PoolCalculatorExecutor
from .core.constants import AGENT_NAME, AGENT_DESCRIPTION


def main():
    """Start the Pool Calculator Agent server."""
    print(f"🧮 Starting Pool Calculator Agent (ADK + A2A) on http://0.0.0.0:9996")
    print(f"   Agent: {AGENT_NAME}")
    print(f"   Description: {AGENT_DESCRIPTION}")
    print(f"   Port: 9996")
    print(f"   Features: Process liquidity/slot0 data, perform calculations, provide LLM insights")

    # Create A2A server
    app = create_a2a_server(
        id=AGENT_NAME.lower(),
        agent_executor=PoolCalculatorExecutor(),
        agent_card=AgentCard(
            name=AGENT_NAME,
            description=AGENT_DESCRIPTION,
            instructions="Process liquidity and slot0 data to perform calculations and provide insights.",
        ),
        agent_skill=AgentSkill(
            name=AGENT_NAME,
            description=AGENT_DESCRIPTION,
            examples=[
                "Calculate price from sqrtPriceX96 for USDT/WETH pool",
                "What's the swap output for 1000 USDT in this pool?",
                "Analyze the health of this liquidity pool",
            ],
        ),
    )

    # Run server
    uvicorn.run(app, host="0.0.0.0", port=9996)


if __name__ == "__main__":
    main()

