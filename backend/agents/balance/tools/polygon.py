from typing import Optional
from web3 import Web3

from lib.shared.blockchain.tokens.constants import POLYGON_TOKENS  # noqa: E402
from lib.shared.blockchain.balance import (  # noqa: E402
    get_token_balance_polygon,
    get_multiple_token_balances_polygon,
    get_native_matic_balance,
)
from lib.shared.blockchain.utils import get_web3_instance, ERC20_ABI  # noqa: E402
from .shared_utils import (  # noqa: E402
    convert_shared_result_to_agent_format,
    build_success_response,
    build_error_response,
    create_token_balance_error_entry,
)


def _resolve_token_symbol_from_address(token_address: str) -> Optional[str]:
    """Resolve token symbol from token address efficiently.

    Args:
        token_address: Token address or symbol

    Returns:
        Token symbol if found, None otherwise
    """
    # Check if token_address is already a symbol
    token_address_upper = token_address.upper()
    if token_address_upper in POLYGON_TOKENS:
        return token_address_upper

    # Check if token_address matches a token address (case-insensitive)
    token_address_lower = token_address.lower()
    for symbol, token_data in POLYGON_TOKENS.items():
        if token_data["address"].lower() == token_address_lower:
            return symbol

    return None


def _resolve_token_address(token_address: str) -> str:
    """Resolve token symbol to address if needed."""
    if token_address.upper() in POLYGON_TOKENS:
        return POLYGON_TOKENS[token_address.upper()]["address"]
    return token_address


def _validate_and_checksum_token_address(w3: Web3, token_address: str) -> str:
    """Validate and convert token address to checksum format."""
    token_address = _resolve_token_address(token_address)
    if not w3.is_address(token_address):
        raise ValueError(f"Invalid token address: {token_address}")
    return w3.to_checksum_address(token_address)


def _fetch_token_balance_data(
    w3: Web3, account_address: str, token_address: str
) -> dict:
    """Fetch token balance data from contract (for unknown tokens)."""
    try:
        token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
        balance_raw = token_contract.functions.balanceOf(account_address).call()

        # Get decimals with fallback
        try:
            decimals = token_contract.functions.decimals().call()
        except Exception:
            decimals = 18

        # Get symbol with fallback
        try:
            symbol = token_contract.functions.symbol().call()
        except Exception:
            symbol = "UNKNOWN"

        balance_float = balance_raw / (10**decimals)
        return {
            "token_type": "token",
            "token_symbol": symbol,
            "token_address": token_address,
            "balance": str(balance_float),
            "balance_raw": str(balance_raw),
            "decimals": decimals,
        }
    except Exception as e:
        # Use default decimals if we couldn't fetch them
        return create_token_balance_error_entry(
            token_address, "UNKNOWN", str(e), decimals=18
        )


def _get_token_balance(w3: Web3, account_address: str, token_address: str) -> dict:
    """Get token balance for account using shared balance tools."""
    # Resolve token symbol from address efficiently
    token_symbol = _resolve_token_symbol_from_address(token_address)

    if token_symbol:
        # Use shared balance tool
        result = get_token_balance_polygon(account_address, token_symbol)
        if "error" not in result:
            return convert_shared_result_to_agent_format(result)
        else:
            return {
                "token_type": "token",
                "token_symbol": result["token_symbol"],
                "token_address": POLYGON_TOKENS[token_symbol]["address"],
                "balance": "0",
                "balance_raw": "0",
                "decimals": result.get("decimals", 18),
                "error": result.get("error", "Unknown error"),
            }

    # Fallback to original implementation for unknown tokens
    token_address = _validate_and_checksum_token_address(w3, token_address)
    return _fetch_token_balance_data(w3, account_address, token_address)


def _get_all_token_balances(w3: Web3, account_address: str) -> list:
    """Get balances for all tokens in POLYGON_TOKENS using shared balance tools.

    Uses batch function for better performance.
    """
    # Get all token symbols
    token_symbols = list(POLYGON_TOKENS.keys())

    # Use batch function for better performance
    results = get_multiple_token_balances_polygon(account_address, token_symbols)

    balances = []
    for i, result in enumerate(results):
        token_symbol = token_symbols[i]

        if "error" not in result:
            # Convert shared tool format to agent format
            balances.append(convert_shared_result_to_agent_format(result))
        else:
            # Include error entry
            balances.append(
                {
                    "token_type": "token",
                    "token_symbol": result.get("token_symbol", token_symbol),
                    "token_address": POLYGON_TOKENS.get(token_symbol, {}).get(
                        "address", "0x0"
                    ),
                    "balance": "0",
                    "balance_raw": "0",
                    "decimals": 18,
                    "error": result.get("error", "Unknown error"),
                }
            )
    return balances


def get_balance_polygon(
    account_address: str, token_address: Optional[str] = None
) -> dict:
    """Get token balance for an account on Polygon chain.

    Args:
        account_address: The wallet address to check balance for
        token_address: Optional token address. If not provided, returns native MATIC
                      and all token balances. Can be a token symbol (e.g., 'USDC')
                      or token address.

    Returns:
        Dictionary with balance information including native and token balances.
    """
    # Ensure account_address is a string
    if not account_address or not isinstance(account_address, str):
        return build_error_response(
            "polygon",
            str(account_address) if account_address else "unknown",
            ValueError("Invalid account address provided"),
        )

    try:
        w3 = get_web3_instance("polygon")
        if not w3.is_connected():
            raise ConnectionError("Failed to connect to Polygon RPC")

        # Validate and checksum address
        if not w3.is_address(account_address):
            raise ValueError(f"Invalid account address: {account_address}")
        account_address = w3.to_checksum_address(account_address)

        balances = []
        # Get native MATIC balance using shared tool
        native_balance = get_native_matic_balance(account_address)
        if isinstance(native_balance, dict):
            balances.append(native_balance)

        if token_address:
            token_balance = _get_token_balance(w3, account_address, token_address)
            if isinstance(token_balance, dict):
                balances.append(token_balance)
        else:
            all_balances = _get_all_token_balances(w3, account_address)
            if isinstance(all_balances, list):
                balances.extend(all_balances)

        result = build_success_response("polygon", account_address, balances)
        # Ensure result is always a valid dict
        if not isinstance(result, dict):
            return build_error_response(
                "polygon", account_address, ValueError("Invalid response format")
            )
        return result
    except Exception as e:
        error_result = build_error_response("polygon", account_address, e)
        # Ensure error result is always a valid dict
        if not isinstance(error_result, dict):
            return {
                "type": "balance",
                "chain": "polygon",
                "account_address": str(account_address)
                if account_address
                else "unknown",
                "error": f"Error: {str(e)}",
                "balances": [],
                "total_usd_value": "$0.00",
            }
        return error_result
