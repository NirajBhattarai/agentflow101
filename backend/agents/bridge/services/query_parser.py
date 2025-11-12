"""
Query parsing utilities for bridge agent.

Handles extraction of bridge parameters from user queries.
"""

import re
from typing import Optional, Tuple
from ..core.constants import (
    DEFAULT_SOURCE_CHAIN,
    DEFAULT_DESTINATION_CHAIN,
    DEFAULT_TOKEN,
    DEFAULT_AMOUNT,
    CHAIN_HEDERA,
    CHAIN_POLYGON,
)


def extract_account_address(query: str) -> Optional[str]:
    """Extract account address from query."""
    hedera_match = re.search(r"0\.0\.\d+", query)
    if hedera_match:
        return hedera_match.group()
    evm_match = re.search(r"0x[a-fA-F0-9]{40}", query)
    if evm_match:
        return evm_match.group()
    return None


def extract_chains(query: str) -> Tuple[str, str, bool]:
    """Extract source and destination chains from query. Returns (source, destination, chains_specified)."""
    query_lower = query.lower()
    source = None
    destination = None
    
    # Look for "from X to Y" pattern
    from_to_match = re.search(r"from\s+(\w+)\s+to\s+(\w+)", query_lower)
    if from_to_match:
        source_str = from_to_match.group(1)
        dest_str = from_to_match.group(2)
        if "hedera" in source_str:
            source = CHAIN_HEDERA
        elif "polygon" in source_str:
            source = CHAIN_POLYGON
        if "hedera" in dest_str:
            destination = CHAIN_HEDERA
        elif "polygon" in dest_str:
            destination = CHAIN_POLYGON
    
    # Look for "X to Y" pattern
    if not source or not destination:
        to_match = re.search(r"(\w+)\s+to\s+(\w+)", query_lower)
        if to_match:
            source_str = to_match.group(1)
            dest_str = to_match.group(2)
            if "hedera" in source_str and not source:
                source = CHAIN_HEDERA
            elif "polygon" in source_str and not source:
                source = CHAIN_POLYGON
            if "hedera" in dest_str and not destination:
                destination = CHAIN_HEDERA
            elif "polygon" in dest_str and not destination:
                destination = CHAIN_POLYGON
    
    # If only one chain found, infer the other
    if source and not destination:
        destination = CHAIN_POLYGON if source == CHAIN_HEDERA else CHAIN_HEDERA
    elif destination and not source:
        source = CHAIN_POLYGON if destination == CHAIN_HEDERA else CHAIN_HEDERA
    
    if source and destination:
        return source, destination, True
    return DEFAULT_SOURCE_CHAIN, DEFAULT_DESTINATION_CHAIN, False


def _get_all_token_symbols() -> list:
    """Get all available token symbols for bridging."""
    # EtaBridge only supports USDC
    return ["USDC"]


def extract_token_symbol(query: str) -> Optional[str]:
    """Extract token symbol from query."""
    all_tokens = _get_all_token_symbols()
    query_upper = query.upper()
    for token in all_tokens:
        if token in query_upper:
            return token
    return None


def extract_amount(query: str) -> str:
    """Extract amount from query."""
    amount_match = re.search(r"(\d+\.?\d*)", query)
    return amount_match.group(1) if amount_match else DEFAULT_AMOUNT


def parse_bridge_query(query: str) -> dict:
    """Parse bridge query and extract all parameters."""
    if not query or not query.strip():
        query = f"Bridge {DEFAULT_AMOUNT} {DEFAULT_TOKEN} from {DEFAULT_SOURCE_CHAIN} to {DEFAULT_DESTINATION_CHAIN}"
    account_address = extract_account_address(query)
    source_chain, destination_chain, chains_specified = extract_chains(query)
    token_symbol = extract_token_symbol(query)
    amount = extract_amount(query)
    return {
        "source_chain": source_chain,
        "destination_chain": destination_chain,
        "chains_specified": chains_specified,
        "token_symbol": token_symbol or DEFAULT_TOKEN,
        "amount": amount,
        "account_address": account_address,
    }

