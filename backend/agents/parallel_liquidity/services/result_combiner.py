"""
Result combination utilities for parallel liquidity agent.

Handles combining liquidity results from multiple chains.
"""

import json
from typing import Optional
from ..core.models.liquidity import LiquidityPair, StructuredParallelLiquidity
from ..core.constants import (
    DEFAULT_HEDERA_FEE_BPS,
    DEFAULT_POLYGON_FEE_BPS,
    DEFAULT_ETHEREUM_FEE_BPS,
)


def parse_tvl(tvl_str: str) -> float:
    """Parse TVL string like '$1,200,000' to float."""
    if isinstance(tvl_str, (int, float)):
        return float(tvl_str)

    if not isinstance(tvl_str, str):
        return 0.0

    # Remove $ and commas
    cleaned = tvl_str.replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0


def process_hedera_results(
    hedera_result: dict, base: str, quote: str
) -> list[LiquidityPair]:
    """Process Hedera liquidity results into LiquidityPair objects."""
    pairs = []
    if not hedera_result:
        return pairs

    if isinstance(hedera_result, str):
        try:
            hedera_result = json.loads(hedera_result)
        except (json.JSONDecodeError, ValueError):
            return pairs

    if isinstance(hedera_result, dict):
        pools = hedera_result.get("pools", [])
        for pool in pools:
            pairs.append(
                LiquidityPair(
                    base=base,
                    quote=quote,
                    pool_address=pool.get("pool_address", ""),
                    dex=pool.get("dex", "SaucerSwap"),
                    tvl_usd=parse_tvl(pool.get("tvl", "$0")),
                    reserve_base=float(pool.get("liquidity", 0)) / 2,
                    reserve_quote=float(pool.get("liquidity", 0)) / 2,
                    fee_bps=DEFAULT_HEDERA_FEE_BPS,
                    chain="hedera",
                )
            )
    return pairs


def process_polygon_results(
    polygon_result: dict, base: str, quote: str
) -> list[LiquidityPair]:
    """Process Polygon liquidity results into LiquidityPair objects."""
    pairs = []
    if not polygon_result:
        print(f"⚠️  No Polygon result provided for {base}/{quote}")
        return pairs

    if isinstance(polygon_result, str):
        try:
            polygon_result = json.loads(polygon_result)
        except (json.JSONDecodeError, ValueError):
            print(f"⚠️  Failed to parse Polygon result as JSON")
            return pairs

    if isinstance(polygon_result, dict):
        pools = polygon_result.get("pools", [])
        print(f"📊 Processing {len(pools)} Polygon pools for {base}/{quote}")
        for pool in pools:
            # Skip pools with errors
            if pool.get("error"):
                continue
                
            # Extract liquidity and slot0 data
            liquidity_value = pool.get("liquidity")
            slot0_data = pool.get("slot0")
            
            # Use token balances if available, otherwise estimate from liquidity
            token0_balance = pool.get("token0_balance_formatted")
            token1_balance = pool.get("token1_balance_formatted")
            
            if token0_balance and token1_balance:
                try:
                    reserve_base = float(token0_balance)
                    reserve_quote = float(token1_balance)
                except (ValueError, TypeError):
                    reserve_base = 0.0
                    reserve_quote = 0.0
            else:
                # Fallback: estimate from liquidity (divide by 2)
                try:
                    liquidity_float = float(liquidity_value) if liquidity_value else 0.0
                    reserve_base = liquidity_float / 2
                    reserve_quote = liquidity_float / 2
                except (ValueError, TypeError):
                    reserve_base = 0.0
                    reserve_quote = 0.0
            
            # Calculate TVL (simple estimate: sum of reserves)
            tvl_usd = reserve_base + reserve_quote
            
            # Get fee from pool or use default
            fee_bps = pool.get("fee", DEFAULT_POLYGON_FEE_BPS)
            if isinstance(fee_bps, float):
                fee_bps = int(fee_bps)
            
            pairs.append(
                LiquidityPair(
                    base=base,
                    quote=quote,
                    pool_address=pool.get("pool_address", ""),
                    dex=pool.get("dex", "Uniswap V3"),
                    tvl_usd=tvl_usd,
                    reserve_base=reserve_base,
                    reserve_quote=reserve_quote,
                    fee_bps=fee_bps,
                    chain="polygon",
                    liquidity=liquidity_value,
                    slot0=slot0_data,
                )
            )
    return pairs


def process_ethereum_results(
    ethereum_result: dict, base: str, quote: str
) -> list[LiquidityPair]:
    """Process Ethereum liquidity results into LiquidityPair objects."""
    pairs = []
    if not ethereum_result:
        print(f"⚠️  No Ethereum result provided for {base}/{quote}")
        return pairs

    if isinstance(ethereum_result, str):
        try:
            ethereum_result = json.loads(ethereum_result)
        except (json.JSONDecodeError, ValueError):
            print(f"⚠️  Failed to parse Ethereum result as JSON")
            return pairs

    if isinstance(ethereum_result, dict):
        pools = ethereum_result.get("pools", [])
        print(f"📊 Processing {len(pools)} Ethereum pools for {base}/{quote}")
        for pool in pools:
            # Skip pools with errors
            if pool.get("error"):
                continue
                
            # Extract liquidity and slot0 data
            liquidity_value = pool.get("liquidity")
            slot0_data = pool.get("slot0")
            
            # Use token balances if available, otherwise estimate from liquidity
            token0_balance = pool.get("token0_balance_formatted")
            token1_balance = pool.get("token1_balance_formatted")
            
            if token0_balance and token1_balance:
                try:
                    reserve_base = float(token0_balance)
                    reserve_quote = float(token1_balance)
                except (ValueError, TypeError):
                    reserve_base = 0.0
                    reserve_quote = 0.0
            else:
                # Fallback: estimate from liquidity (divide by 2)
                try:
                    liquidity_float = float(liquidity_value) if liquidity_value else 0.0
                    reserve_base = liquidity_float / 2
                    reserve_quote = liquidity_float / 2
                except (ValueError, TypeError):
                    reserve_base = 0.0
                    reserve_quote = 0.0
            
            # Calculate TVL (simple estimate: sum of reserves)
            tvl_usd = reserve_base + reserve_quote
            
            # Get fee from pool or use default
            fee_bps = pool.get("fee", DEFAULT_ETHEREUM_FEE_BPS)
            if isinstance(fee_bps, float):
                fee_bps = int(fee_bps)
            
            pairs.append(
                LiquidityPair(
                    base=base,
                    quote=quote,
                    pool_address=pool.get("pool_address", ""),
                    dex=pool.get("dex", "Uniswap V3"),
                    tvl_usd=tvl_usd,
                    reserve_base=reserve_base,
                    reserve_quote=reserve_quote,
                    fee_bps=fee_bps,
                    chain="ethereum",
                    liquidity=liquidity_value,
                    slot0=slot0_data,
                )
            )
    return pairs


def combine_results(
    token_pair: str,
    hedera_result: Optional[dict],
    polygon_result: Optional[dict],
    ethereum_result: Optional[dict] = None,
) -> dict:
    """Combine results from Hedera, Polygon, and Ethereum into unified response."""
    base, quote = token_pair.split("/")

    hedera_pairs = process_hedera_results(hedera_result, base, quote)
    polygon_pairs = process_polygon_results(polygon_result, base, quote)
    ethereum_pairs = process_ethereum_results(ethereum_result, base, quote) if ethereum_result else []
    all_pairs = hedera_pairs + polygon_pairs + ethereum_pairs

    # Always include all chains, even if empty, so frontend knows which chains were queried
    chains_dict = {
        "hedera": {
            "pairs": [p.model_dump() for p in hedera_pairs],
            "total_pools": len(hedera_pairs),
        },
        "polygon": {
            "pairs": [p.model_dump() for p in polygon_pairs],
            "total_pools": len(polygon_pairs),
        },
        "ethereum": {
            "pairs": [p.model_dump() for p in ethereum_pairs],
            "total_pools": len(ethereum_pairs),
        },
    }
    
    # Debug logging
    print(f"📊 Combined results for {token_pair}:")
    print(f"  - Hedera pairs: {len(hedera_pairs)}")
    print(f"  - Polygon pairs: {len(polygon_pairs)}")
    print(f"  - Ethereum pairs: {len(ethereum_pairs)}")
    print(f"  - Total pairs: {len(all_pairs)}")

    response = StructuredParallelLiquidity(
        type="parallel_liquidity",
        token_pair=token_pair,
        chains=chains_dict,
        hedera_pairs=hedera_pairs,
        polygon_pairs=polygon_pairs,
        all_pairs=all_pairs,
    )

    return response.model_dump()
