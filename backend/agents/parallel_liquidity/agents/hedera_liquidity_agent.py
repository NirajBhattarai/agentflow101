"""
Hedera Liquidity Agent

Independent sub-agent for fetching liquidity from Hedera chain (SaucerSwap).
"""

import os
from google.adk.agents.llm_agent import LlmAgent  # noqa: E402
from lib.shared.blockchain.liquidity import get_liquidity_hedera  # noqa: E402


def build_hedera_liquidity_agent() -> LlmAgent:
    """Build Hedera liquidity sub-agent."""
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    hedera_agent = LlmAgent(
        name="HederaLiquidityAgent",
        model=model_name,
        instruction="""You are a Hedera liquidity query agent specializing in Hedera chain (SaucerSwap DEX).

When given a token pair query like "Get liquidity for ETH/USDT" or "HBAR/USDC":
1. Extract the base token from the pair (the token before the "/" - e.g., "ETH" from "ETH/USDT", "HBAR" from "HBAR/USDC")
2. Call get_liquidity_hedera tool with the base token symbol (e.g., "ETH", "HBAR", "USDC")
3. The tool will return liquidity data with pools information
4. Return the tool's result as-is (it's already JSON format)

Example: For query "Get liquidity for HBAR/USDC", extract "HBAR" and call get_liquidity_hedera("HBAR")

Output *only* the JSON result from the tool. Store your result with output_key="hedera_liquidity".
        """,
        description="Fetches liquidity from Hedera chain (SaucerSwap)",
        tools=[get_liquidity_hedera],
        output_key="hedera_liquidity",
    )

    return hedera_agent
