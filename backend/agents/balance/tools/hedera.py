import os
from typing import Optional
import requests
from lib.shared.blockchain.tokens.constants import HEDERA_TOKENS  # noqa: E402
from lib.shared.blockchain.balance import get_token_balance_hedera  # noqa: E402

# Hedera REST API endpoints
HEDERA_MAINNET_API = "https://mainnet-public.mirrornode.hedera.com"
HEDERA_TESTNET_API = "https://testnet.mirrornode.hedera.com"


def _get_hedera_api_base() -> str:
    """Get Hedera API base URL."""
    network = os.getenv("HEDERA_NETWORK", "mainnet")
    if network.lower() == "testnet":
        return HEDERA_TESTNET_API
    return HEDERA_MAINNET_API


def _resolve_evm_to_hedera(evm_address: str, api_base: str) -> str:
    """Resolve EVM address to Hedera account ID."""
    resp = requests.get(f"{api_base}/api/v1/accounts/{evm_address}", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        account_id = data.get("account") or data.get("account_id")
        if account_id:
            return str(account_id)
    raise ValueError(
        f"Unable to resolve Hedera account from EVM address: {evm_address}"
    )


def _validate_hedera_format(identifier: str) -> str:
    """Validate Hedera account ID format (0.0.x)."""
    parts = identifier.split(".")
    if len(parts) != 3:
        raise ValueError(
            f"Invalid Hedera account ID format: {identifier}. Expected format: 0.0.123456"
        )
    try:
        int(parts[0])
        int(parts[1])
        int(parts[2])
    except ValueError:
        raise ValueError(f"Invalid Hedera account ID format: {identifier}")
    return identifier


def _resolve_hedera_account_id(identifier: str, api_base: str) -> str:
    """Accepts Hedera account in '0.0.x' or EVM '0x...' and returns '0.0.x'."""
    identifier = identifier.strip()
    if identifier.startswith("0x") and len(identifier) == 42:
        return _resolve_evm_to_hedera(identifier, api_base)
    return _validate_hedera_format(identifier)


def _parse_hedera_account_id(account_id: str) -> str:
    """Validate strict Hedera account ID format (0.0.x). Does not resolve EVM."""
    return _validate_hedera_format(account_id)


def _format_hbar_balance(tinybar: int) -> str:
    """Format HBAR balance from tinybar to HBAR (1 HBAR = 100,000,000 tinybar)."""
    hbar_balance = tinybar / 100_000_000
    return str(hbar_balance)


def _get_account_identifier(account_address: str, account_id: str) -> str:
    """Get account identifier for API calls."""
    if account_address.startswith("0x"):
        return account_address
    return account_id


def _create_native_balance_entry(balance_tinybar: int) -> dict:
    """Create native HBAR balance entry."""
    return {
        "token_type": "native",
        "token_symbol": "HBAR",
        "token_address": "0.0.0",
        "balance": _format_hbar_balance(balance_tinybar),
        "balance_raw": str(balance_tinybar),
        "decimals": 8,
    }


def _create_native_balance_error_entry(error: str) -> dict:
    """Create native HBAR balance entry with error."""
    return {
        "token_type": "native",
        "token_symbol": "HBAR",
        "token_address": "0.0.0",
        "balance": "0",
        "balance_raw": "0",
        "decimals": 8,
        "error": error,
    }


def _get_native_balance(api_base: str, account_identifier: str) -> dict:
    """Get native HBAR balance for account."""
    try:
        account_url = f"{api_base}/api/v1/accounts/{account_identifier}"
        response = requests.get(account_url, timeout=10)
        if response.status_code == 200:
            account_data = response.json()
            balance_tinybar = account_data.get("balance", {}).get("balance", 0)
            return _create_native_balance_entry(balance_tinybar)
        error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
        return _create_native_balance_error_entry(error_msg)
    except Exception as e:
        return _create_native_balance_error_entry(str(e))


def _create_token_id_to_symbol_map() -> dict:
    """Create reverse mapping: token_id -> symbol."""
    return {token_id: symbol for symbol, token_id in HEDERA_TOKENS.items()}


def _format_token_balance(balance_raw: int, decimals: int) -> str:
    """Format token balance from raw to human-readable format."""
    return str(balance_raw / (10**decimals))


def _create_token_balance_entry(
    token_id: str, symbol: str, balance_raw: int, decimals: int
) -> dict:
    """Create token balance entry."""
    return {
        "token_type": "token",
        "token_symbol": symbol,
        "token_address": token_id,
        "balance": _format_token_balance(balance_raw, decimals),
        "balance_raw": str(balance_raw),
        "decimals": decimals,
    }


def _create_token_balance_error_entry(token_id: str, symbol: str, error: str) -> dict:
    """Create token balance entry with error."""
    return {
        "token_type": "token",
        "token_symbol": symbol,
        "token_address": token_id,
        "balance": "0",
        "balance_raw": "0",
        "decimals": 6,
        "error": error,
    }


def _get_token_symbol(token_id: str, token: dict, token_id_to_symbol: dict) -> str:
    """Get token symbol from mapping or token data."""
    if token_id in token_id_to_symbol:
        return token_id_to_symbol[token_id]
    return token.get("symbol", "UNKNOWN")


def _process_single_token(token: dict, token_id_to_symbol: dict) -> Optional[dict]:
    """Process a single token and return balance entry if non-zero."""
    token_id = token.get("token_id")
    balance_raw = int(token.get("balance", 0))
    if balance_raw == 0:
        return None
    symbol = _get_token_symbol(token_id, token, token_id_to_symbol)
    decimals = token.get("decimals", 6)
    return _create_token_balance_entry(token_id, symbol, balance_raw, decimals)


def _process_account_tokens(account_tokens: list, token_id_to_symbol: dict) -> list:
    """Process tokens from account and return balance entries."""
    balances = []
    for token in account_tokens:
        entry = _process_single_token(token, token_id_to_symbol)
        if entry:
            balances.append(entry)
    return balances


def _get_account_token_balances(api_base: str, account_identifier: str) -> list:
    """Get all token balances for account from Mirror Node API."""
    try:
        token_balance_url = f"{api_base}/api/v1/accounts/{account_identifier}/tokens"
        response = requests.get(token_balance_url, timeout=10)
        if response.status_code == 200:
            tokens_data = response.json()
            account_tokens = tokens_data.get("tokens", [])
            token_id_to_symbol = _create_token_id_to_symbol_map()
            return _process_account_tokens(account_tokens, token_id_to_symbol)
        return []
    except Exception:
        return []


def _resolve_token_address(token_address: str) -> str:
    """Resolve token symbol to address if needed."""
    if token_address.upper() in HEDERA_TOKENS:
        return HEDERA_TOKENS[token_address.upper()]["tokenid"]
    return token_address


def _find_token_in_response(account_tokens: list, token_id: str) -> Optional[dict]:
    """Find specific token in account tokens response."""
    for token in account_tokens:
        if token.get("token_id") == token_id:
            return token
    return None


def _get_symbol_for_token_id(token_id: str) -> str:
    """Get symbol for token ID from mapping or fallback."""
    token_id_to_symbol = _create_token_id_to_symbol_map()
    return token_id_to_symbol.get(token_id) or token_id.split(".")[-1]


def _fetch_token_balance_data(
    api_base: str, account_identifier: str, token_id: str
) -> dict:
    """Fetch token balance data from API."""
    token_balance_url = (
        f"{api_base}/api/v1/accounts/{account_identifier}/tokens?token.id={token_id}"
    )
    response = requests.get(token_balance_url, timeout=10)
    if response.status_code == 200:
        tokens_data = response.json()
        account_tokens = tokens_data.get("tokens", [])
        token_id_to_symbol = _create_token_id_to_symbol_map()
        token = _find_token_in_response(account_tokens, token_id)
        if token:
            balance_raw = int(token.get("balance", 0))
            symbol = token_id_to_symbol.get(token_id) or token.get("symbol", "UNKNOWN")
            decimals = token.get("decimals", 6)
            return _create_token_balance_entry(token_id, symbol, balance_raw, decimals)
    symbol = _get_symbol_for_token_id(token_id)
    return _create_token_balance_entry(token_id, symbol, 0, 6)


def _get_specific_token_balance(
    api_base: str, account_identifier: str, token_id: str
) -> dict:
    """Get balance for a specific token using shared balance tools."""
    # Try to resolve token symbol from token_id
    token_symbol = None
    for symbol, token_data in HEDERA_TOKENS.items():
        if token_data["tokenid"] == token_id:
            token_symbol = symbol
            break

    # If token_id is a symbol, use it directly
    if token_id.upper() in HEDERA_TOKENS:
        token_symbol = token_id.upper()

    account_id = account_identifier if not account_identifier.startswith("0x") else None
    if not account_id:
        # If EVM address, need to resolve to Hedera account ID first
        account_id = _resolve_evm_to_hedera(account_identifier, api_base)

    if token_symbol:
        # Use shared balance tool
        result = get_token_balance_hedera(account_id, token_symbol)
        if "error" not in result and "token_address" in result:
            return {
                "token_type": "token",
                "token_symbol": result["token_symbol"],
                "token_address": result["token_address"],
                "balance": result["balance"],
                "balance_raw": result["balance_raw"],
                "decimals": result.get("decimals", 6),
            }
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
            return _create_token_balance_error_entry(
                HEDERA_TOKENS[token_symbol]["tokenid"],
                symbol,
                result.get("error", "Unknown error"),
            )

    # Fallback to original implementation for unknown tokens
    try:
        return _fetch_token_balance_data(api_base, account_identifier, token_id)
    except Exception as e:
        symbol = _get_symbol_for_token_id(token_id)
        return _create_token_balance_error_entry(token_id, symbol, str(e))


def _get_all_token_balances(api_base: str, account_identifier: str) -> list:
    """Get balances for all tokens in HEDERA_TOKENS using shared balance tools."""
    balances = []
    account_id = account_identifier if not account_identifier.startswith("0x") else None
    if not account_id:
        # If EVM address, need to resolve to Hedera account ID first
        account_id = _resolve_evm_to_hedera(account_identifier, api_base)

    for token_symbol in HEDERA_TOKENS.keys():
        if token_symbol == "HBAR":  # Skip native HBAR (handled separately)
            continue
        result = get_token_balance_hedera(account_id, token_symbol)
        if "error" not in result and "token_address" in result:
            # Convert shared tool format to agent format
            balances.append(
                {
                    "token_type": "token",
                    "token_symbol": result["token_symbol"],
                    "token_address": result["token_address"],
                    "balance": result["balance"],
                    "balance_raw": result["balance_raw"],
                    "decimals": result.get("decimals", 6),
                }
            )
        elif "error" not in result:
            # Balance is 0, still include entry
            balances.append(
                {
                    "token_type": "token",
                    "token_symbol": result["token_symbol"],
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
                    "token_symbol": result["token_symbol"],
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


def _build_success_response(account_id: str, balances: list) -> dict:
    """Build successful balance response."""
    return {
        "type": "balance",
        "chain": "hedera",
        "account_address": account_id,
        "balances": balances,
        "total_usd_value": "$0.00",
    }


def _build_error_response(account_address: str, error: Exception) -> dict:
    """Build error balance response."""
    return {
        "type": "balance",
        "chain": "hedera",
        "account_address": account_address,
        "error": str(error),
        "balances": [],
        "total_usd_value": "$0.00",
    }


def get_balance_hedera(
    account_address: str, token_address: Optional[str] = None
) -> dict:
    """Get token balance for an account on Hedera chain.

    Args:
        account_address: The Hedera account ID (e.g., '0.0.123456')
        token_address: Optional token address. If not provided, returns native HBAR
                      and all token balances. Can be a token symbol (e.g., 'USDC')
                      or token address.

    Returns:
        Dictionary with balance information including native and token balances.
    """
    try:
        api_base = _get_hedera_api_base()
        account_id = _resolve_hedera_account_id(account_address, api_base)
        account_identifier = _get_account_identifier(account_address, account_id)
        balances = []
        balances.append(_get_native_balance(api_base, account_identifier))
        if token_address:
            token_id = _resolve_token_address(token_address)
            balances.append(
                _get_specific_token_balance(api_base, account_identifier, token_id)
            )
        else:
            balances.extend(_get_all_token_balances(api_base, account_identifier))
        return _build_success_response(account_id, balances)
    except Exception as e:
        return _build_error_response(account_address, e)
