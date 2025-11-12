from typing import Optional
from .polygon import get_balance_polygon
from .hedera import get_balance_hedera


def get_balance_all_chains(
    account_address: str, token_address: Optional[str] = None
) -> dict:
    """Get token balance for an account across all supported chains.

    Args:
        account_address: The wallet/account address to check balance for.
                        Note: Polygon uses 0x format, Hedera uses 0.0.123 format.
                        This function will try both formats, but it's recommended
                        to use chain-specific addresses when possible.
        token_address: Optional token address or symbol

    Returns:
        Dictionary with balance information across all chains.
    """
    try:
        # Fetch balances from all chains
        # Note: Each chain will validate its own address format
        polygon_result = get_balance_polygon(account_address, token_address)
        hedera_result = get_balance_hedera(account_address, token_address)

        # Ensure both results are valid dicts
        if not isinstance(polygon_result, dict):
            polygon_result = {
                "type": "balance",
                "chain": "polygon",
                "account_address": account_address,
                "error": "Invalid response from Polygon balance tool",
                "balances": [],
                "total_usd_value": "$0.00",
            }

        if not isinstance(hedera_result, dict):
            hedera_result = {
                "type": "balance",
                "chain": "hedera",
                "account_address": account_address,
                "error": "Invalid response from Hedera balance tool",
                "balances": [],
                "total_usd_value": "$0.00",
            }

        # Calculate total USD value (placeholder - in production, use price oracles)
        # This would require fetching token prices from an oracle service
        total_usd_value = "$0.00"  # Placeholder - real implementation needed

        return {
            "type": "balance_summary",
            "account_address": account_address,
            "token_address": token_address,
            "chains": {
                "polygon": polygon_result,
                "hedera": hedera_result,
            },
            "total_usd_value": total_usd_value,
        }
    except Exception as e:
        # Always return a valid dict, even on error
        return {
            "type": "balance_summary",
            "account_address": account_address or "unknown",
            "token_address": token_address,
            "chains": {
                "polygon": {
                    "type": "balance",
                    "chain": "polygon",
                    "account_address": account_address or "unknown",
                    "error": f"Error fetching Polygon balance: {str(e)}",
                    "balances": [],
                    "total_usd_value": "$0.00",
                },
                "hedera": {
                    "type": "balance",
                    "chain": "hedera",
                    "account_address": account_address or "unknown",
                    "error": f"Error fetching Hedera balance: {str(e)}",
                    "balances": [],
                    "total_usd_value": "$0.00",
                },
            },
            "total_usd_value": "$0.00",
            "error": str(e),
        }
