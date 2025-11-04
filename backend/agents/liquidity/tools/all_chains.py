from .ethereum import get_liquidity_ethereum
from .bsc import get_liquidity_bsc
from .polygon import get_liquidity_polygon
from .hedera import get_liquidity_hedera


def get_liquidity_all_chains(token_address: str) -> dict:
    """Get liquidity information from all supported chains."""
    return {
        "type": "liquidity_summary",
        "token_address": token_address,
        "chains": {
            "ethereum": get_liquidity_ethereum(token_address),
            "bsc": get_liquidity_bsc(token_address),
            "polygon": get_liquidity_polygon(token_address),
            "hedera": get_liquidity_hedera(token_address)
        },
        "total_tvl": "$8,550,000",
        "total_volume_24h": "$455,000"
    }

