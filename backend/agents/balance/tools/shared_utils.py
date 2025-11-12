"""
Shared utilities for balance agent tools.

Contains common functions used across different chain implementations.
"""

from typing import Dict, List


def convert_shared_result_to_agent_format(result: dict, default_decimals: int = 18) -> dict:
    """Convert shared balance tool result to agent format.
    
    Args:
        result: Result from shared balance tool
        default_decimals: Default decimals if not in result (18 for EVM, 6 for Hedera)
        
    Returns:
        Dictionary in agent format
    """
    return {
        "token_type": "token",
        "token_symbol": result["token_symbol"],
        "token_address": result.get("token_address", "0x0"),
        "balance": result.get("balance", "0"),
        "balance_raw": result.get("balance_raw", "0"),
        "decimals": result.get("decimals", default_decimals),
    }


def build_success_response(chain: str, account_address: str, balances: list) -> dict:
    """Build successful balance response.
    
    Args:
        chain: Chain name (hedera, polygon, etc.)
        account_address: Account address
        balances: List of balance entries
        
    Returns:
        Success response dictionary
    """
    return {
        "type": "balance",
        "chain": chain,
        "account_address": account_address,
        "balances": balances,
        "total_usd_value": "$0.00",
    }


def build_error_response(chain: str, account_address: str, error: Exception) -> dict:
    """Build error balance response.
    
    Args:
        chain: Chain name (hedera, polygon, etc.)
        account_address: Account address
        error: Exception that occurred
        
    Returns:
        Error response dictionary
    """
    return {
        "type": "balance",
        "chain": chain,
        "account_address": account_address,
        "error": str(error),
        "balances": [],
        "total_usd_value": "$0.00",
    }


def create_token_balance_error_entry(
    token_address: str, symbol: str, error: str, decimals: int = 18
) -> dict:
    """Create token balance entry with error.
    
    Args:
        token_address: Token address
        symbol: Token symbol
        error: Error message
        decimals: Token decimals (default: 18)
        
    Returns:
        Error entry dictionary
    """
    return {
        "token_type": "token",
        "token_symbol": symbol,
        "token_address": token_address,
        "balance": "0",
        "balance_raw": "0",
        "decimals": decimals,
        "error": error,
    }

