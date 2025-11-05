import os
from pathlib import Path
from dotenv import load_dotenv
"""Ensure environment variables are loaded from backend/.env if present."""
# Load default .env discovery first (current working directory or parents)
load_dotenv()
# # Additionally, try the repo's backend/.env explicitly relative to this file
# _backend_env = Path(__file__).resolve().parents[3] / ".env"
# if _backend_env.exists():
#     load_dotenv(dotenv_path=_backend_env, override=False)
from typing import Optional
from web3 import Web3
from .constants import POLYGON_TOKENS
from .abi.erc20 import ERC20_ABI


def _get_web3_instance() -> Web3:
    """Get Web3 instance connected to Polygon RPC."""
    rpc_url = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
    # print(f"Using RPC URL: {rpc_url}", flush=True)
    return Web3(Web3.HTTPProvider(rpc_url))


def _format_balance(balance_wei: int, decimals: int) -> str:
    """Format balance from wei to human-readable format."""
    balance_float = balance_wei / (10**decimals)
    return str(balance_float)


def get_balance_polygon(
    account_address: str, token_address: Optional[str] = None
) -> dict:
    """Get token balance for an account on Polygon chain.

    Args:
        account_address: The wallet address to check balance for (must be checksummed)
        token_address: Optional token address. If not provided, returns native MATIC balance.
                      Can be a token symbol (e.g., 'USDC') or token address.

    Returns:
        Dictionary with balance information including native and token balances.
    """
    try:
        w3 = _get_web3_instance()

        # Validate connection
        if not w3.is_connected():
            raise ConnectionError("Failed to connect to Polygon RPC")

        # Validate account address
        if not w3.is_address(account_address):
            raise ValueError(f"Invalid account address: {account_address}")

        # Convert to checksum address
        account_address = w3.to_checksum_address(account_address)

        balances = []

        # Get native MATIC balance (always included)
        try:
            matic_balance_wei = w3.eth.get_balance(account_address)
            balances.append(
                {
                    "token_type": "native",
                    "token_symbol": "MATIC",
                    "token_address": "0x0000000000000000000000000000000000000000",
                    "balance": _format_balance(matic_balance_wei, 18),
                    "balance_raw": str(matic_balance_wei),
                    "decimals": 18,
                }
            )
        except Exception as e:
            # If native balance fetch fails, still include it with error
            balances.append(
                {
                    "token_type": "native",
                    "token_symbol": "MATIC",
                    "token_address": "0x0000000000000000000000000000000000000000",
                    "balance": "0",
                    "balance_raw": "0",
                    "decimals": 18,
                    "error": str(e),
                }
            )

        # Get token balance (if token_address provided)
        if token_address:
            # Look up token address if a symbol is provided
            if token_address.upper() in POLYGON_TOKENS:
                token_address = POLYGON_TOKENS[token_address.upper()]

            # Validate token address
            if not w3.is_address(token_address):
                raise ValueError(f"Invalid token address: {token_address}")

            token_address = w3.to_checksum_address(token_address)

            try:
                # Create contract instance
                token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)

                # Get token balance
                balance_raw = token_contract.functions.balanceOf(account_address).call()

                # Get token decimals
                try:
                    decimals = token_contract.functions.decimals().call()
                except Exception:
                    decimals = 18  # Default to 18 if decimals() fails

                # Get token symbol
                try:
                    symbol = token_contract.functions.symbol().call()
                except Exception:
                    symbol = "UNKNOWN"

                balances.append(
                    {
                        "token_type": "token",
                        "token_symbol": symbol,
                        "token_address": token_address,
                        "balance": _format_balance(balance_raw, decimals),
                        "balance_raw": str(balance_raw),
                        "decimals": decimals,
                    }
                )
            except Exception as e:
                # If token balance fetch fails, include error
                balances.append(
                    {
                        "token_type": "token",
                        "token_symbol": "UNKNOWN",
                        "token_address": token_address,
                        "balance": "0",
                        "balance_raw": "0",
                        "decimals": 18,
                        "error": str(e),
                    }
                )

        # Calculate approximate USD value (simplified - in production, use price oracles)
        # This is a placeholder - real implementation should fetch token prices
        total_usd_value = "$0.00"  # Placeholder

        return {
            "type": "balance",
            "chain": "polygon",
            "account_address": account_address,
            "balances": balances,
            "total_usd_value": total_usd_value,
        }

    except Exception as e:
        # Return error response
        return {
            "type": "balance",
            "chain": "polygon",
            "account_address": account_address,
            "error": str(e),
            "balances": [],
            "total_usd_value": "$0.00",
        }
