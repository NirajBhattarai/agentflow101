"""
Response building utilities for bridge agent.

Handles construction of bridge responses.
"""

import json
from ..core.constants import (
    RESPONSE_TYPE,
    DEFAULT_CONFIRMATION_THRESHOLD,
    ERROR_CHAIN_NOT_SPECIFIED,
    ERROR_TOKEN_NOT_FOUND,
    ERROR_INVALID_BRIDGE_PAIR,
)


def build_chain_selection_response() -> str:
    """Build response asking user to select chains."""
    message = (
        "To proceed with the bridge, please specify source and destination chains:\n\n"
        "• **Hedera** - Bridge from/to Hedera network\n"
        "• **Polygon** - Bridge from/to Polygon network\n\n"
        "Please specify both source and destination chains (e.g., 'bridge from Hedera to Polygon')."
    )
    return json.dumps(
        {
            "type": RESPONSE_TYPE,
            "requires_chain_selection": True,
            "message": message,
            "supported_chains": ["hedera", "polygon"],
        },
        indent=2,
    )


def build_error_response(
    error_type: str,
    source_chain: str = None,
    destination_chain: str = None,
    token_symbol: str = None,
) -> str:
    """Build error response."""
    error_messages = {
        "chain_not_specified": ERROR_CHAIN_NOT_SPECIFIED,
        "token_not_found": ERROR_TOKEN_NOT_FOUND,
        "invalid_bridge_pair": ERROR_INVALID_BRIDGE_PAIR,
    }
    error_msg = error_messages.get(error_type, "Unknown error")
    if error_type == "token_not_found":
        error_msg += ". Please specify clearly, e.g., 'bridge USDC from Hedera to Polygon'"
    elif error_type == "invalid_bridge_pair":
        error_msg += ". Only Hedera <-> Polygon bridges are supported via EtaBridge"
    return json.dumps(
        {
            "type": RESPONSE_TYPE,
            "source_chain": source_chain or "unknown",
            "destination_chain": destination_chain or "unknown",
            "token_symbol": token_symbol or "unknown",
            "error": error_msg,
        },
        indent=2,
    )


def build_bridge_response(bridge_data: dict) -> dict:
    """Build bridge response from bridge data."""
    return {
        "type": RESPONSE_TYPE,
        "source_chain": bridge_data["source_chain"],
        "destination_chain": bridge_data["destination_chain"],
        "token_symbol": bridge_data["token_symbol"],
        "amount": bridge_data["amount"],
        "account_address": bridge_data.get("account_address"),
        "balance_check": bridge_data.get("balance_check"),
        "bridge_options": bridge_data.get("bridge_options"),
        "transaction": bridge_data.get("transaction"),
        "requires_confirmation": bridge_data.get("requires_confirmation", False),
        "confirmation_threshold": DEFAULT_CONFIRMATION_THRESHOLD,
        "amount_exceeds_threshold": bridge_data.get("amount_exceeds_threshold", False),
    }

