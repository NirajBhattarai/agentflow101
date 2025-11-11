"""
Response building utilities for swap agent.

Handles construction of swap responses.
"""

import json
from ..core.constants import (
    RESPONSE_TYPE,
    DEFAULT_CONFIRMATION_THRESHOLD,
    ERROR_CHAIN_NOT_SPECIFIED,
    ERROR_TOKEN_IN_NOT_FOUND,
    ERROR_TOKEN_OUT_NOT_FOUND,
)


def build_chain_selection_response() -> str:
    """Build response asking user to select chain."""
    message = (
        "To proceed with the swap, please specify which blockchain you'd like to swap on:\n\n"
        "• **Hedera** - For swapping HBAR, USDC, USDT, and other Hedera tokens\n"
        "• **Polygon** - For swapping MATIC, USDC, USDT, and other Polygon tokens\n\n"
        "Please select a chain and provide your swap details."
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
    error_type: str, chain: str = None, token_in: str = None, token_out: str = None
) -> str:
    """Build error response."""
    error_messages = {
        "chain_not_specified": ERROR_CHAIN_NOT_SPECIFIED,
        "token_in_not_found": ERROR_TOKEN_IN_NOT_FOUND,
        "token_out_not_found": ERROR_TOKEN_OUT_NOT_FOUND,
    }
    error_msg = error_messages.get(error_type, "Unknown error")
    if error_type == "token_in_not_found":
        error_msg += ". Please specify clearly, e.g., 'swap USDC to HBAR' or 'swap 0.2 USDC to HBAR'"
    elif error_type == "token_out_not_found":
        error_msg += ". Please specify clearly, e.g., 'swap USDC to HBAR' or 'swap 0.2 USDC to HBAR'"
    return json.dumps(
        {
            "type": RESPONSE_TYPE,
            "chain": chain or "unknown",
            "token_in_symbol": token_in or "unknown",
            "token_out_symbol": token_out or "unknown",
            "error": error_msg,
        },
        indent=2,
    )


def build_swap_response(swap_data: dict) -> dict:
    """Build swap response from swap data."""
    return {
        "type": RESPONSE_TYPE,
        "chain": swap_data["chain"],
        "token_in_symbol": swap_data["token_in_symbol"],
        "token_out_symbol": swap_data["token_out_symbol"],
        "amount_in": swap_data["amount_in"],
        "account_address": swap_data.get("account_address"),
        "balance_check": swap_data.get("balance_check"),
        "swap_options": None,
        "transaction": swap_data.get("transaction"),
        "requires_confirmation": False,
        "confirmation_threshold": DEFAULT_CONFIRMATION_THRESHOLD,
        "amount_exceeds_threshold": False,
    }
