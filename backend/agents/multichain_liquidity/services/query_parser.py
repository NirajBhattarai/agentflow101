"""
Query parser for Multi-Chain Liquidity Agent.

Extracts token pair and chain information from natural language queries.
"""

import re
from typing import Optional, Dict


def extract_token_pair(query: str) -> Optional[str]:
    """
    Extract token pair from query.

    Examples:
    - "Get liquidity for ETH/USDT" -> "ETH/USDT"
    - "Get liquidity from ETH USDT" -> "ETH/USDT"
    - "Show me liquidity for HBAR/USDC" -> "HBAR/USDC"
    """
    # Pattern 1: "TOKEN1/TOKEN2" format
    pair_match = re.search(r"\b([A-Z]{2,10})/([A-Z]{2,10})\b", query.upper())
    if pair_match:
        return f"{pair_match.group(1)}/{pair_match.group(2)}"

    # Pattern 2: "TOKEN1 TOKEN2" or "TOKEN1 and TOKEN2"
    tokens = re.findall(r"\b([A-Z]{2,10})\b", query.upper())
    if len(tokens) >= 2:
        # Filter out common words
        common_words = {
            "GET",
            "LIQUIDITY",
            "FOR",
            "FROM",
            "SHOW",
            "ME",
            "ALL",
            "CHAIN",
            "CHAINS",
        }
        filtered = [t for t in tokens if t not in common_words]
        if len(filtered) >= 2:
            return f"{filtered[0]}/{filtered[1]}"

    return None


def extract_chain(query: str) -> Optional[str]:
    """
    Extract chain name from query.

    Returns: "hedera", "polygon", "ethereum", or None (for "all")
    """
    query_lower = query.lower()

    if "hedera" in query_lower:
        return "hedera"
    if "polygon" in query_lower:
        return "polygon"
    # Only match full 'ethereum' mention; avoid matching token 'ETH' in pairs
    if "ethereum" in query_lower:
        return "ethereum"
    if "all" in query_lower or "every" in query_lower:
        return "all"

    return None


def parse_query(query: str) -> Dict:
    """
    Parse liquidity query to extract token pair and chain.

    Returns:
        Dictionary with:
        - token_pair: Optional[str] - Token pair if found (e.g., "ETH/USDT")
        - chain: Optional[str] - Chain if specified ("hedera", "polygon", "ethereum", "all")
    """
    token_pair = extract_token_pair(query)
    chain = extract_chain(query)

    return {
        "token_pair": token_pair,
        "chain": chain,
        "query": query,
    }
