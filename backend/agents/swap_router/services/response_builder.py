"""
Response builder for Swap Router Agent.
"""

import json
from typing import Optional
from ..core.models.routing import SwapRouterRecommendation
from ..core.exceptions import SwapRouterError


def build_routing_response(recommendation: SwapRouterRecommendation) -> str:
    """
    Build and serialize routing response.

    Args:
        recommendation: SwapRouterRecommendation object

    Returns:
        JSON string response
    """
    try:
        return json.dumps(recommendation.model_dump(), indent=2)
    except Exception as e:
        raise SwapRouterError(f"Failed to build response: {e}") from e


def build_error_response(error: str, details: Optional[dict] = None) -> str:
    """
    Build error response.

    Args:
        error: Error message
        details: Additional error details

    Returns:
        JSON string error response
    """
    response = {
        "type": "swap_router",
        "error": error,
        "details": details or {},
    }
    return json.dumps(response, indent=2)
