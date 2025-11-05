import os
from typing import Optional
import requests
from .constants import HEDERA_TOKENS

# Hedera REST API endpoints
HEDERA_MAINNET_API = "https://mainnet-public.mirrornode.hedera.com"
HEDERA_TESTNET_API = "https://testnet.mirrornode.hedera.com"


def _get_hedera_api_base() -> str:
    """Get Hedera API base URL."""
    network = os.getenv("HEDERA_NETWORK", "mainnet")
    if network.lower() == "testnet":
        return HEDERA_TESTNET_API
    return HEDERA_MAINNET_API


def _resolve_hedera_account_id(identifier: str, api_base: str) -> str:
    """Accepts Hedera account in '0.0.x' or EVM '0x...' and returns '0.0.x'."""
    identifier = identifier.strip()
    if identifier.startswith("0x") and len(identifier) == 42:
        # Resolve EVM address to Hedera account via Mirror Node
        resp = requests.get(f"{api_base}/api/v1/accounts/{identifier}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            account_id = data.get("account") or data.get("account_id")
            if account_id:
                return str(account_id)
        raise ValueError(f"Unable to resolve Hedera account from EVM address: {identifier}")

    # Validate 0.0.x format
    parts = identifier.split(".")
    if len(parts) != 3:
        raise ValueError(
            f"Invalid Hedera account ID format: {identifier}. Expected format: 0.0.123456"
        )
    try:
        int(parts[0]); int(parts[1]); int(parts[2])
    except ValueError:
        raise ValueError(f"Invalid Hedera account ID format: {identifier}")
    return identifier


def _parse_hedera_account_id(account_id: str) -> str:
    """Validate strict Hedera account ID format (0.0.x). Does not resolve EVM."""
    parts = account_id.split(".")
    if len(parts) != 3:
        raise ValueError(
            f"Invalid Hedera account ID format: {account_id}. Expected format: 0.0.123456"
        )
    try:
        int(parts[0]); int(parts[1]); int(parts[2])
    except ValueError:
        raise ValueError(f"Invalid Hedera account ID format: {account_id}")
    return account_id


def _format_hbar_balance(tinybar: int) -> str:
    """Format HBAR balance from tinybar to HBAR (1 HBAR = 100,000,000 tinybar)."""
    hbar_balance = tinybar / 100_000_000
    return str(hbar_balance)


def get_balance_hedera(
    account_address: str, token_address: Optional[str] = None
) -> dict:
    """Get token balance for an account on Hedera chain.

    Args:
        account_address: The Hedera account ID (e.g., '0.0.123456')
        token_address: Optional token address. If not provided, returns native HBAR balance.
                      Can be a token symbol (e.g., 'USDC') or token address.

    Returns:
        Dictionary with balance information including native and token balances.
    """
    try:
        api_base = _get_hedera_api_base()
        account_id = _resolve_hedera_account_id(account_address, api_base)

        balances = []

        # Get native HBAR balance
        try:
            account_url = f"{api_base}/api/v1/accounts/{account_id}"
            response = requests.get(account_url, timeout=10)

            if response.status_code == 200:
                account_data = response.json()
                balance_tinybar = account_data.get("balance", {}).get("balance", 0)

                balances.append(
                    {
                        "token_type": "native",
                        "token_symbol": "HBAR",
                        "token_address": "0.0.0",
                        "balance": _format_hbar_balance(balance_tinybar),
                        "balance_raw": str(balance_tinybar),
                        "decimals": 8,
                    }
                )
            else:
                # If account not found or error, set balance to 0
                balances.append(
                    {
                        "token_type": "native",
                        "token_symbol": "HBAR",
                        "token_address": "0.0.0",
                        "balance": "0",
                        "balance_raw": "0",
                        "decimals": 8,
                        "error": f"HTTP {response.status_code}: {response.text[:100]}",
                    }
                )
        except Exception as e:
            balances.append(
                {
                    "token_type": "native",
                    "token_symbol": "HBAR",
                    "token_address": "0.0.0",
                    "balance": "0",
                    "balance_raw": "0",
                    "decimals": 8,
                    "error": str(e),
                }
            )

        # Get token balance (if token_address provided)
        if token_address:
            # Look up token address if a symbol is provided
            if token_address.upper() in HEDERA_TOKENS:
                token_address = HEDERA_TOKENS[token_address.upper()]

            # Validate token address format
            try:
                _resolve_hedera_account_id(token_address, api_base)
            except ValueError:
                raise ValueError(f"Invalid Hedera token address: {token_address}")

            try:
                # Get token balance for the account
                token_balance_url = f"{api_base}/api/v1/accounts/{account_id}/tokens"
                response = requests.get(token_balance_url, timeout=10)

                if response.status_code == 200:
                    tokens_data = response.json()
                    token_balance = None

                    # Find the token in the list
                    for token in tokens_data.get("tokens", []):
                        if token.get("token_id") == token_address:
                            balance_raw = int(token.get("balance", 0))
                            # Hedera tokens typically have 6-8 decimals
                            decimals = token.get("decimals", 6)
                            balance = str(balance_raw / (10**decimals))

                            token_balance = {
                                "token_type": "token",
                                "token_symbol": token.get("symbol", "UNKNOWN"),
                                "token_address": token_address,
                                "balance": balance,
                                "balance_raw": str(balance_raw),
                                "decimals": decimals,
                            }
                            break

                    if token_balance:
                        balances.append(token_balance)
                    else:
                        # Token not found in account, return zero balance
                        balances.append(
                            {
                                "token_type": "token",
                                "token_symbol": "UNKNOWN",
                                "token_address": token_address,
                                "balance": "0",
                                "balance_raw": "0",
                                "decimals": 6,
                            }
                        )
                else:
                    balances.append(
                        {
                            "token_type": "token",
                            "token_symbol": "UNKNOWN",
                            "token_address": token_address,
                            "balance": "0",
                            "balance_raw": "0",
                            "decimals": 6,
                            "error": f"HTTP {response.status_code}: {response.text[:100]}",
                        }
                    )
            except Exception as e:
                balances.append(
                    {
                        "token_type": "token",
                        "token_symbol": "UNKNOWN",
                        "token_address": token_address,
                        "balance": "0",
                        "balance_raw": "0",
                        "decimals": 6,
                        "error": str(e),
                    }
                )

        # Calculate approximate USD value (placeholder)
        total_usd_value = "$0.00"  # Placeholder

        return {
            "type": "balance",
            "chain": "hedera",
            "account_address": account_id,
            "balances": balances,
            "total_usd_value": total_usd_value,
        }

    except Exception as e:
        # Return error response
        return {
            "type": "balance",
            "chain": "hedera",
            "account_address": account_address,
            "error": str(e),
            "balances": [],
            "total_usd_value": "$0.00",
        }
