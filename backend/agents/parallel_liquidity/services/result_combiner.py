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
        return pairs

    if isinstance(polygon_result, str):
        try:
            polygon_result = json.loads(polygon_result)
        except (json.JSONDecodeError, ValueError):
            return pairs

    if isinstance(polygon_result, dict):
        pools = polygon_result.get("pools", [])
        for pool in pools:
            pairs.append(
                LiquidityPair(
                    base=base,
                    quote=quote,
                    pool_address=pool.get("pool_address", ""),
                    dex=pool.get("dex", "QuickSwap"),
                    tvl_usd=parse_tvl(pool.get("tvl", "$0")),
                    reserve_base=float(pool.get("liquidity", 0)) / 2,
                    reserve_quote=float(pool.get("liquidity", 0)) / 2,
                    fee_bps=DEFAULT_POLYGON_FEE_BPS,
                    chain="polygon",
                )
            )
    return pairs


def combine_results(
    token_pair: str,
    hedera_result: Optional[dict],
    polygon_result: Optional[dict],
) -> dict:
    """Combine results from Hedera and Polygon into unified response."""
    base, quote = token_pair.split("/")

    hedera_pairs = process_hedera_results(hedera_result, base, quote)
    polygon_pairs = process_polygon_results(polygon_result, base, quote)
    all_pairs = hedera_pairs + polygon_pairs

    response = StructuredParallelLiquidity(
        type="parallel_liquidity",
        token_pair=token_pair,
        chains={
            "hedera": {
                "pairs": [p.model_dump() for p in hedera_pairs],
                "total_pools": len(hedera_pairs),
            },
            "polygon": {
                "pairs": [p.model_dump() for p in polygon_pairs],
                "total_pools": len(polygon_pairs),
            },
        },
        hedera_pairs=hedera_pairs,
        polygon_pairs=polygon_pairs,
        all_pairs=all_pairs,
    )

    return response.model_dump()
