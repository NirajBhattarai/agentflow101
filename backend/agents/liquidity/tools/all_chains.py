from lib.shared.blockchain.liquidity import (  # noqa: E402
    get_liquidity_polygon,
    get_liquidity_hedera,
)


def get_liquidity_all_chains(token_address: str) -> dict:
    """Get liquidity information from all supported chains."""
    return {
        "type": "liquidity_summary",
        "token_address": token_address,
        "chains": {
            "polygon": get_liquidity_polygon(token_address),
            "hedera": get_liquidity_hedera(token_address),
        },
        "total_tvl": "$2,850,000",
        "total_volume_24h": "$130,000",
    }
