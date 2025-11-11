"""
Query parsing utilities for parallel liquidity agent.

Handles extraction of token pairs from user queries.
"""

import re
from typing import Optional


def extract_token_pair(query: str) -> Optional[str]:
    """Extract token pair from query (e.g., 'ETH/USDT', 'HBAR/USDC')."""
    if not query:
        return None

    query_upper = query.upper()

    # Pattern to match token pairs: ETH/USDT, HBAR/USDC, etc.
    patterns = [
        r"([A-Z0-9]{2,})/([A-Z0-9]{2,})",  # ETH/USDT, HBAR/USDC
        r"pair[:\s=]+([A-Z0-9]+)/([A-Z0-9]+)",  # pair: ETH/USDT
        r"for\s+([A-Z0-9]+)/([A-Z0-9]+)",  # for ETH/USDT
    ]

    for pattern in patterns:
        match = re.search(pattern, query_upper)
        if match:
            if len(match.groups()) >= 2:
                return f"{match.group(1)}/{match.group(2)}"
            elif "/" in match.group(0):
                return match.group(0)

    return None
