"""
Response building utilities for balance agent.

Handles construction of balance responses for different chains.
"""

from ..tools import get_balance_polygon, get_balance_hedera
from ..core.constants import (
    RESPONSE_TYPE,
    CHAIN_POLYGON,
    CHAIN_HEDERA,
    CHAIN_ALL,
    DEFAULT_TOTAL_USD_VALUE,
)


def add_chain_to_balances(balances: list, chain: str) -> list:
    """Add chain information to balance entries."""
    return [{**balance, "chain": chain} for balance in balances]


def build_all_chains_response(account_address: str) -> dict:
    """Build response for all chains."""
    polygon_result = get_balance_polygon(account_address)
    hedera_result = get_balance_hedera(account_address)
    polygon_balances = add_chain_to_balances(
        polygon_result.get("balances", []), CHAIN_POLYGON
    )
    hedera_balances = add_chain_to_balances(
        hedera_result.get("balances", []), CHAIN_HEDERA
    )
    return {
        "type": RESPONSE_TYPE,
        "chain": CHAIN_ALL,
        "account_address": account_address,
        "balances": [*hedera_balances, *polygon_balances],
        "total_usd_value": DEFAULT_TOTAL_USD_VALUE,
    }


def build_unknown_chain_response(chain: str, account_address: str) -> dict:
    """Build response for unknown chain."""
    return {
        "type": RESPONSE_TYPE,
        "chain": chain,
        "account_address": account_address,
        "balances": [],
        "total_usd_value": DEFAULT_TOTAL_USD_VALUE,
    }


def build_balance_response(chain: str, account_address: str) -> dict:
    """Build balance response based on chain.

    Routes to appropriate chain tool or combines results for all chains.
    The tools already return the correct format, so we just route to them.
    """
    if chain == CHAIN_POLYGON:
        return get_balance_polygon(account_address)
    if chain == CHAIN_HEDERA:
        return get_balance_hedera(account_address)
    if chain == CHAIN_ALL:
        return build_all_chains_response(account_address)
    return build_unknown_chain_response(chain, account_address)
