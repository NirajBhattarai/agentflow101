import os
from typing import Optional

from dotenv import load_dotenv
from web3 import Web3

from .abi.erc20 import ERC20_ABI
from lib.shared.blockchain.tokens.constants import POLYGON_TOKENS  # noqa: E402
from lib.shared.blockchain.balance import get_token_balance_polygon  # noqa: E402

"""Ensure environment variables are loaded from backend/.env if present."""
# Load default .env discovery first (current working directory or parents)
load_dotenv()
# # Additionally, try the repo's backend/.env explicitly relative to this file
# _backend_env = Path(__file__).resolve().parents[3] / ".env"
# if _backend_env.exists():
#     load_dotenv(dotenv_path=_backend_env, override=False)


def _get_web3_instance() -> Web3:
    """Get Web3 instance connected to Polygon RPC."""
    rpc_url = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
    # print(f"Using RPC URL: {rpc_url}", flush=True)
    return Web3(Web3.HTTPProvider(rpc_url))


def _format_balance(balance_wei: int, decimals: int) -> str:
    """Format balance from wei to human-readable format."""
    balance_float = balance_wei / (10**decimals)
    return str(balance_float)


def _validate_web3_connection(w3: Web3) -> None:
    """Validate Web3 connection."""
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to Polygon RPC")


def _validate_and_checksum_address(w3: Web3, address: str) -> str:
    """Validate and convert address to checksum format."""
    if not w3.is_address(address):
        raise ValueError(f"Invalid account address: {address}")
    return w3.to_checksum_address(address)


def _create_native_balance_entry(balance_wei: int) -> dict:
    """Create native MATIC balance entry."""
    return {
        "token_type": "native",
        "token_symbol": "MATIC",
        "token_address": "0x0000000000000000000000000000000000000000",
        "balance": _format_balance(balance_wei, 18),
        "balance_raw": str(balance_wei),
        "decimals": 18,
    }


def _create_native_balance_error_entry(error: Exception) -> dict:
    """Create native MATIC balance entry with error."""
    return {
        "token_type": "native",
        "token_symbol": "MATIC",
        "token_address": "0x0000000000000000000000000000000000000000",
        "balance": "0",
        "balance_raw": "0",
        "decimals": 18,
        "error": str(error),
    }


def _get_native_balance(w3: Web3, account_address: str) -> dict:
    """Get native MATIC balance for account."""
    try:
        balance_wei = w3.eth.get_balance(account_address)
        return _create_native_balance_entry(balance_wei)
    except Exception as e:
        return _create_native_balance_error_entry(e)


def _resolve_token_address(token_address: str) -> str:
    """Resolve token symbol to address if needed."""
    if token_address.upper() in POLYGON_TOKENS:
        return POLYGON_TOKENS[token_address.upper()]["address"]
    return token_address


def _get_token_decimals(token_contract) -> int:
    """Get token decimals with fallback to 18."""
    try:
        return token_contract.functions.decimals().call()
    except Exception:
        return 18


def _get_token_symbol(token_contract) -> str:
    """Get token symbol with fallback to UNKNOWN."""
    try:
        return token_contract.functions.symbol().call()
    except Exception:
        return "UNKNOWN"


def _create_token_balance_entry(
    symbol: str, token_address: str, balance_raw: int, decimals: int
) -> dict:
    """Create token balance entry."""
    return {
        "token_type": "token",
        "token_symbol": symbol,
        "token_address": token_address,
        "balance": _format_balance(balance_raw, decimals),
        "balance_raw": str(balance_raw),
        "decimals": decimals,
    }


def _create_token_balance_error_entry(token_address: str, error: Exception) -> dict:
    """Create token balance entry with error."""
    return {
        "token_type": "token",
        "token_symbol": "UNKNOWN",
        "token_address": token_address,
        "balance": "0",
        "balance_raw": "0",
        "decimals": 18,
        "error": str(error),
    }


def _validate_and_checksum_token_address(w3: Web3, token_address: str) -> str:
    """Validate and convert token address to checksum format."""
    token_address = _resolve_token_address(token_address)
    if not w3.is_address(token_address):
        raise ValueError(f"Invalid token address: {token_address}")
    return w3.to_checksum_address(token_address)


def _fetch_token_balance_data(
    w3: Web3, account_address: str, token_address: str
) -> dict:
    """Fetch token balance data from contract."""
    token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
    balance_raw = token_contract.functions.balanceOf(account_address).call()
    decimals = _get_token_decimals(token_contract)
    symbol = _get_token_symbol(token_contract)
    return _create_token_balance_entry(symbol, token_address, balance_raw, decimals)


def _get_token_balance(w3: Web3, account_address: str, token_address: str) -> dict:
    """Get token balance for account using shared balance tools."""
    # Try to resolve token symbol from address
    token_symbol = None
    for symbol, token_data in POLYGON_TOKENS.items():
        if token_data["address"].lower() == token_address.lower():
            token_symbol = symbol
            break
    
    # If token_address is a symbol, use it directly
    if token_address.upper() in POLYGON_TOKENS:
        token_symbol = token_address.upper()
    
    if token_symbol:
        # Use shared balance tool
        result = get_token_balance_polygon(account_address, token_symbol)
        if "error" not in result:
            return {
                "token_type": "token",
                "token_symbol": result["token_symbol"],
                "token_address": result["token_address"],
                "balance": result["balance"],
                "balance_raw": result["balance_raw"],
                "decimals": result["decimals"],
            }
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
    try:
        return _fetch_token_balance_data(w3, account_address, token_address)
    except Exception as e:
        return _create_token_balance_error_entry(token_address, e)


def _build_success_response(account_address: str, balances: list) -> dict:
    """Build successful balance response."""
    return {
        "type": "balance",
        "chain": "polygon",
        "account_address": account_address,
        "balances": balances,
        "total_usd_value": "$0.00",
    }


def _build_error_response(account_address: str, error: Exception) -> dict:
    """Build error balance response."""
    return {
        "type": "balance",
        "chain": "polygon",
        "account_address": account_address,
        "error": str(error),
        "balances": [],
        "total_usd_value": "$0.00",
    }


def _get_all_token_balances(w3: Web3, account_address: str) -> list:
    """Get balances for all tokens in POLYGON_TOKENS using shared balance tools."""
    balances = []
    for token_symbol in POLYGON_TOKENS.keys():
        result = get_token_balance_polygon(account_address, token_symbol)
        if "error" not in result:
            # Convert shared tool format to agent format
            balances.append({
                "token_type": "token",
                "token_symbol": result["token_symbol"],
                "token_address": result["token_address"],
                "balance": result["balance"],
                "balance_raw": result["balance_raw"],
                "decimals": result["decimals"],
            })
        else:
            # Include error entry
            balances.append({
                "token_type": "token",
                "token_symbol": result["token_symbol"],
                "token_address": POLYGON_TOKENS.get(token_symbol, {}).get("address", "0x0"),
                "balance": "0",
                "balance_raw": "0",
                "decimals": 18,
                "error": result.get("error", "Unknown error"),
            })
    return balances


def get_balance_polygon(
    account_address: str, token_address: Optional[str] = None
) -> dict:
    """Get token balance for an account on Polygon chain.

    Args:
        account_address: The wallet address to check balance for (must be checksummed)
        token_address: Optional token address. If not provided, returns native MATIC
                      and all token balances. Can be a token symbol (e.g., 'USDC')
                      or token address.

    Returns:
        Dictionary with balance information including native and token balances.
    """
    try:
        w3 = _get_web3_instance()
        _validate_web3_connection(w3)
        account_address = _validate_and_checksum_address(w3, account_address)
        balances = []
        balances.append(_get_native_balance(w3, account_address))
        if token_address:
            balances.append(_get_token_balance(w3, account_address, token_address))
        else:
            balances.extend(_get_all_token_balances(w3, account_address))
        return _build_success_response(account_address, balances)
    except Exception as e:
        return _build_error_response(account_address, e)
