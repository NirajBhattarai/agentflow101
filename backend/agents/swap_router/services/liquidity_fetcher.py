"""
Liquidity Fetcher Service

Fetches liquidity data using the multichain_liquidity agent.
"""

import json
from typing import Dict, List
from ..core.models.routing import PoolData
from agents.multichain_liquidity.agent import MultiChainLiquidityAgent


async def fetch_liquidity_from_multichain_agent(
    token_pair: str,
    session_id: str = "swap_router_session",
) -> Dict:
    """
    Fetch liquidity data using multichain_liquidity agent.

    Args:
        token_pair: Token pair (e.g., "ETH/USDT")
        session_id: Session ID for the agent call

    Returns:
        Dictionary with liquidity data from multichain_liquidity agent
    """
    agent = MultiChainLiquidityAgent()
    query = f"Get liquidity for {token_pair}"

    try:
        response = await agent.invoke(query, session_id)
        data = json.loads(response)
        return data
    except Exception as e:
        print(f"Error fetching liquidity from multichain agent: {e}")
        return {}


def convert_liquidity_to_pool_data(
    liquidity_data: Dict,
    token_in: str,
    token_out: str,
) -> Dict[str, List[PoolData]]:
    """
    Convert multichain_liquidity response to PoolData objects grouped by chain.

    Args:
        liquidity_data: Response from multichain_liquidity agent
        token_in: Input token symbol
        token_out: Output token symbol

    Returns:
        Dictionary mapping chain -> list of PoolData
    """
    pools_by_chain = {
        "ethereum": [],
        "polygon": [],
        "hedera": [],
    }

    # Extract pairs from chains
    chains = liquidity_data.get("chains", {})

    for chain_name, chain_data in chains.items():
        pairs = chain_data.get("pairs", [])

        for pair in pairs:
            # Determine which token is which
            base = pair.get("base", "").upper()
            quote = pair.get("quote", "").upper()
            
            # Normalize token symbols for matching (ETH -> WETH for EVM chains)
            token_in_upper = token_in.upper()
            token_out_upper = token_out.upper()
            
            # Map ETH to WETH for EVM chains
            if chain_name in ["ethereum", "polygon"]:
                if token_in_upper == "ETH":
                    token_in_upper = "WETH"
                if token_out_upper == "ETH":
                    token_out_upper = "WETH"
                if base == "ETH":
                    base = "WETH"
                if quote == "ETH":
                    quote = "WETH"

            # Check if this pair matches our swap direction
            if (base == token_in_upper and quote == token_out_upper) or (
                base == token_out_upper and quote == token_in_upper
            ):
                pool_data = PoolData(
                    chain=chain_name,
                    pool_address=pair.get("pool_address", ""),
                    token0=base,
                    token1=quote,
                    fee_tier=pair.get("fee_bps", 3000),
                    liquidity=pair.get("liquidity"),
                    slot0=pair.get("slot0"),
                    sqrt_price_x96=pair.get("slot0", {}).get("sqrtPriceX96")
                    if pair.get("slot0")
                    else None,
                    tick=pair.get("slot0", {}).get("tick")
                    if pair.get("slot0")
                    else None,
                    reserve_base=pair.get("reserve_base", 0.0),
                    reserve_quote=pair.get("reserve_quote", 0.0),
                    tvl_usd=pair.get("tvl_usd", 0.0),
                )

                pools_by_chain[chain_name].append(pool_data)

    return pools_by_chain
