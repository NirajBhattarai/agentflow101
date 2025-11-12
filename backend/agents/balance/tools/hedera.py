import os
from typing import Optional
from lib.shared.blockchain.tokens.constants import HEDERA_TOKENS  # noqa: E402
from lib.shared.blockchain.balance import (  # noqa: E402
    get_token_balance_hedera,
    get_multiple_token_balances_hedera,
    get_hedera_api_base,
    resolve_hedera_account_id,
    get_account_identifier_for_api,
    get_native_hbar_balance,
)
from .shared_utils import (  # noqa: E402
    convert_shared_result_to_agent_format,
    build_success_response,
    build_error_response,
    create_token_balance_error_entry,
)


def _get_symbol_for_token_id(token_id: str) -> str:
    """Get symbol for token ID from mapping or fallback."""
    # Create reverse mapping on the fly (only used in error cases)
    token_id_to_symbol = {
        token_data["tokenid"]: symbol 
        for symbol, token_data in HEDERA_TOKENS.items()
    }
    return token_id_to_symbol.get(token_id) or token_id.split(".")[-1]


def _resolve_token_symbol_from_id(token_id: str) -> Optional[str]:
    """Resolve token symbol from token ID efficiently.
    
    Args:
        token_id: Token ID or symbol
        
    Returns:
        Token symbol if found, None otherwise
    """
    # Check if token_id is already a symbol
    token_id_upper = token_id.upper()
    if token_id_upper in HEDERA_TOKENS:
        return token_id_upper
    
    # Check if token_id matches a token ID
    for symbol, token_data in HEDERA_TOKENS.items():
        if token_data["tokenid"] == token_id:
            return symbol
    
    return None


def _resolve_token_address(token_address: str) -> str:
    """Resolve token symbol to address if needed."""
    if token_address.upper() in HEDERA_TOKENS:
        return HEDERA_TOKENS[token_address.upper()]["tokenid"]
    return token_address


def _get_specific_token_balance(
    api_base: str, account_identifier: str, token_id: str
) -> dict:
    """Get balance for a specific token using shared balance tools."""
    # Resolve token symbol from token_id efficiently
    token_symbol = _resolve_token_symbol_from_id(token_id)
    
    # Resolve account ID (handles both EVM and Hedera formats)
    account_id = resolve_hedera_account_id(account_identifier, api_base)

    if token_symbol:
        # Use shared balance tool
        result = get_token_balance_hedera(account_id, token_symbol)
        if "error" not in result and "token_address" in result:
            return convert_shared_result_to_agent_format(result, default_decimals=6)
        elif "error" not in result:
            # Balance is 0
            return {
                "token_type": "token",
                "token_symbol": result["token_symbol"],
                "token_address": HEDERA_TOKENS[token_symbol]["tokenid"],
                "balance": "0",
                "balance_raw": "0",
                "decimals": HEDERA_TOKENS[token_symbol].get("decimals", 6),
            }
        else:
            symbol = result.get("token_symbol", token_symbol)
            return create_token_balance_error_entry(
                HEDERA_TOKENS[token_symbol]["tokenid"],
                symbol,
                result.get("error", "Unknown error"),
                decimals=HEDERA_TOKENS[token_symbol].get("decimals", 6),
            )

    # Fallback for unknown tokens - use shared balance tool with token_id as symbol
    try:
        result = get_token_balance_hedera(account_id, token_id)
        if "error" not in result and "token_address" in result:
            return convert_shared_result_to_agent_format(result, default_decimals=6)
        symbol = _get_symbol_for_token_id(token_id)
        return create_token_balance_error_entry(
            token_id, symbol, result.get("error", "Token not found"), decimals=6
        )
    except Exception as e:
        symbol = _get_symbol_for_token_id(token_id)
        return create_token_balance_error_entry(token_id, symbol, str(e), decimals=6)


def _get_all_token_balances(api_base: str, account_identifier: str) -> list:
    """Get balances for all tokens in HEDERA_TOKENS using shared balance tools.
    
    Uses batch function for better performance.
    """
    # Resolve account ID (handles both EVM and Hedera formats)
    account_id = resolve_hedera_account_id(account_identifier, api_base)
    
    # Get all token symbols except HBAR (handled separately)
    token_symbols = [
        symbol for symbol in HEDERA_TOKENS.keys() if symbol != "HBAR"
    ]
    
    # Use batch function for better performance (single API call with pagination)
    results = get_multiple_token_balances_hedera(account_id, token_symbols)
    
    balances = []
    for i, result in enumerate(results):
        token_symbol = token_symbols[i]
        
        if "error" not in result and "token_address" in result:
            # Convert shared tool format to agent format
            balances.append(convert_shared_result_to_agent_format(result, default_decimals=6))
        elif "error" not in result:
            # Balance is 0, still include entry
            balances.append(
                {
                    "token_type": "token",
                    "token_symbol": result.get("token_symbol", token_symbol),
                    "token_address": HEDERA_TOKENS[token_symbol]["tokenid"],
                    "balance": "0",
                    "balance_raw": "0",
                    "decimals": HEDERA_TOKENS[token_symbol].get("decimals", 6),
                }
            )
        else:
            # Include error entry
            balances.append(
                {
                    "token_type": "token",
                    "token_symbol": result.get("token_symbol", token_symbol),
                    "token_address": HEDERA_TOKENS.get(token_symbol, {}).get(
                        "tokenid", "0.0.0"
                    ),
                    "balance": "0",
                    "balance_raw": "0",
                    "decimals": 6,
                    "error": result.get("error", "Unknown error"),
                }
            )
    return balances




def get_balance_hedera(
    account_address: str, token_address: Optional[str] = None
) -> dict:
    """Get token balance for an account on Hedera chain.

    Args:
        account_address: The Hedera account ID (e.g., '0.0.123456') or EVM address (0x...)
        token_address: Optional token address. If not provided, returns native HBAR
                      and all token balances. Can be a token symbol (e.g., 'USDC')
                      or token address.

    Returns:
        Dictionary with balance information including native and token balances.
    """
    # Ensure account_address is a string
    if not account_address or not isinstance(account_address, str):
        return build_error_response(
            "hedera", 
            str(account_address) if account_address else "unknown",
            ValueError("Invalid account address provided")
        )
    
    try:
        # Get network from environment
        network = os.getenv("HEDERA_NETWORK", "mainnet")
        api_base = get_hedera_api_base(network)
        
        # Resolve account ID (handles both EVM and Hedera formats)
        account_id = resolve_hedera_account_id(account_address, api_base)
        
        # Get account identifier for API calls (prefers EVM format if available)
        account_identifier = get_account_identifier_for_api(account_address, account_id)
        
        balances = []
        # Get native HBAR balance using shared tool
        native_balance = get_native_hbar_balance(account_identifier, api_base)
        if isinstance(native_balance, dict):
            balances.append(native_balance)
        
        if token_address:
            token_id = _resolve_token_address(token_address)
            token_balance = _get_specific_token_balance(api_base, account_identifier, token_id)
            if isinstance(token_balance, dict):
                balances.append(token_balance)
        else:
            all_balances = _get_all_token_balances(api_base, account_identifier)
            if isinstance(all_balances, list):
                balances.extend(all_balances)
        
        result = build_success_response("hedera", account_id, balances)
        # Ensure result is always a valid dict
        if not isinstance(result, dict):
            return build_error_response("hedera", account_address, ValueError("Invalid response format"))
        return result
    except Exception as e:
        error_result = build_error_response("hedera", account_address, e)
        # Ensure error result is always a valid dict
        if not isinstance(error_result, dict):
            return {
                "type": "balance",
                "chain": "hedera",
                "account_address": str(account_address) if account_address else "unknown",
                "error": f"Error: {str(e)}",
                "balances": [],
                "total_usd_value": "$0.00",
            }
        return error_result
