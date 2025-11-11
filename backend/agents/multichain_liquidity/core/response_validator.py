"""
Response validation utilities for Multi-Chain Liquidity Agent.
"""

import json
from .constants import RESPONSE_TYPE
from .models.liquidity import StructuredMultiChainLiquidity
from .exceptions import ValidationError


def validate_and_serialize_response(liquidity_data: dict) -> str:
    """Validate and serialize liquidity response to JSON."""
    try:
        validated_liquidity = StructuredMultiChainLiquidity(**liquidity_data)
        return json.dumps(validated_liquidity.model_dump(), indent=2)
    except Exception as e:
        raise ValidationError(
            f"Failed to validate liquidity response: {str(e)}",
            details={"liquidity_data": liquidity_data},
        ) from e


def build_error_response(error: str) -> str:
    """Build error response."""
    response = {
        "type": RESPONSE_TYPE,
        "token_pair": None,
        "chain": None,
        "chains": {
            "hedera": {"pairs": [], "total_pools": 0},
            "polygon": {"pairs": [], "total_pools": 0},
            "ethereum": {"pairs": [], "total_pools": 0},
        },
        "hedera_pairs": [],
        "polygon_pairs": [],
        "ethereum_pairs": [],
        "all_pairs": [],
        "error": error,
    }
    return json.dumps(response, indent=2)
