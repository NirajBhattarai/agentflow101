"""
Polygon Liquidity Agent

Independent sub-agent for fetching liquidity from Polygon chain.
"""

import os
from google.adk.agents.llm_agent import LlmAgent  # noqa: E402
from lib.shared.blockchain.liquidity import get_liquidity_polygon  # noqa: E402


def build_polygon_liquidity_agent() -> LlmAgent:
    """Build Polygon liquidity sub-agent."""
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    polygon_agent = LlmAgent(
        name="PolygonLiquidityAgent",
        model=model_name,
        instruction="""You are a Polygon liquidity query agent specializing in Polygon chain.

When given a token pair query like "Get liquidity for ETH/USDT" or "HBAR/USDC":
1. Extract the base token from the pair (the token before the "/" - e.g., "ETH" from "ETH/USDT", "HBAR" from "HBAR/USDC")
2. Call get_liquidity_polygon tool with the base token symbol (e.g., "ETH", "HBAR", "USDC")
3. The tool will return liquidity data with pools information
4. Return the tool's result as-is (it's already JSON format)

Example: For query "Get liquidity for ETH/USDT", extract "ETH" and call get_liquidity_polygon("ETH")

Output *only* the JSON result from the tool. Store your result with output_key="polygon_liquidity".
        """,
        description="Fetches liquidity from Polygon chain",
        tools=[get_liquidity_polygon],
        output_key="polygon_liquidity",
    )

    return polygon_agent
