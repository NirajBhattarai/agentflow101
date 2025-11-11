"""
Ethereum Liquidity Agent

Independent sub-agent for fetching liquidity from Ethereum chain.
"""

import os
from google.adk.agents.llm_agent import LlmAgent  # noqa: E402
from lib.shared.blockchain.liquidity import get_liquidity_ethereum  # noqa: E402


def build_ethereum_liquidity_agent() -> LlmAgent:
    """Build Ethereum liquidity sub-agent."""
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    ethereum_agent = LlmAgent(
        name="EthereumLiquidityAgent",
        model=model_name,
        instruction="""You are an Ethereum liquidity query agent specializing in Ethereum chain.

When given a token pair query like "Get liquidity for ETH/USDT" or "WETH/USDC":
1. Extract the full token pair from the query (e.g., "ETH/USDT" from "Get liquidity for ETH/USDT")
2. Call get_liquidity_ethereum tool with the full token pair (e.g., "ETH/USDT", "WETH/USDC")
3. The tool will find the pool using WETH and USDT addresses, get liquidity and slot0 data
4. Return the tool's result as-is (it's already JSON format)

Example: For query "Get liquidity for ETH/USDT", extract "ETH/USDT" and call get_liquidity_ethereum("ETH/USDT")

Output *only* the JSON result from the tool. Store your result with output_key="ethereum_liquidity".
        """,
        description="Fetches liquidity from Ethereum chain",
        tools=[get_liquidity_ethereum],
        output_key="ethereum_liquidity",
    )

    return ethereum_agent

