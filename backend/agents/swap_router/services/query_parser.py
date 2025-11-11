"""
Query parser for Swap Router Agent.

Extracts swap parameters from natural language queries.
"""

import re
from typing import Dict


def parse_swap_router_query(query: str) -> Dict:
    """
    Parse swap router query to extract parameters.

    Args:
        query: User query (e.g., "swap 2 million USDT to ETH")

    Returns:
        Dictionary with parsed parameters
    """
    query_lower = query.lower()

    # Extract amount
    amount = None
    amount_str = None

    # Patterns for amounts
    patterns = [
        r"(\d+(?:\.\d+)?)\s*(?:million|m)\s*(?:usdt|usdc|eth|hbar|matic)",
        r"(\d+(?:\.\d+)?)\s*(?:thousand|k)\s*(?:usdt|usdc|eth|hbar|matic)",
        r"(\d+(?:\.\d+)?)\s*(?:billion|b)\s*(?:usdt|usdc|eth|hbar|matic)",
        r"swap\s+(\d+(?:\.\d+)?)\s*(?:million|m|thousand|k|billion|b)?",
        r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:usdt|usdc|eth|hbar|matic)",
    ]

    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            amount_str = match.group(1).replace(",", "")
            try:
                amount = float(amount_str)
                # Check for multipliers
                if "million" in query_lower or "m" in query_lower:
                    amount *= 1000000
                elif "thousand" in query_lower or "k" in query_lower:
                    amount *= 1000
                elif "billion" in query_lower or "b" in query_lower:
                    amount *= 1000000000
                break
            except ValueError:
                continue

    # Extract token pair
    token_in = None
    token_out = None

    # Common token symbols
    tokens = ["USDT", "USDC", "ETH", "HBAR", "MATIC", "WBTC", "DAI", "WETH"]

    # Pattern: "token1 to token2" or "token1/token2"
    pair_patterns = [
        r"(\w+)\s+to\s+(\w+)",
        r"(\w+)\s*/\s*(\w+)",
        r"swap\s+\w+\s+(\w+)\s+to\s+(\w+)",
    ]

    for pattern in pair_patterns:
        match = re.search(pattern, query_lower)
        if match:
            token1 = match.group(1).upper()
            token2 = match.group(2).upper()

            # Normalize token names
            if token1 == "WETH":
                token1 = "ETH"
            if token2 == "WETH":
                token2 = "ETH"

            if token1 in tokens and token2 in tokens:
                token_in = token1
                token_out = token2
                break

    # If amount found but tokens not found, try to extract from context
    if amount and not token_in:
        # Look for tokens near amount
        amount_idx = query_lower.find(amount_str.lower() if amount_str else "")
        if amount_idx >= 0:
            # Look for token after amount
            after_amount = query[amount_idx + len(amount_str or "") :].upper()
            for token in tokens:
                if token in after_amount:
                    token_in = token
                    break

    # Default fallback
    if not token_in:
        token_in = "USDT"
    if not token_out:
        token_out = "ETH"

    return {
        "amount": amount,
        "amount_str": amount_str,
        "token_in": token_in,
        "token_out": token_out,
        "token_pair": f"{token_in}/{token_out}",
        "query": query,
    }
