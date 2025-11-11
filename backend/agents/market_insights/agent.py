"""
Market Insights Agent Definition

An agent that fetches trending tokens and pools across multiple networks.
"""

from typing import Optional

from .core.constants import (
    DEFAULT_USER_ID,
    NETWORK_ETH,
    NETWORK_POLYGON,
    NETWORK_HEDERA,
    SUPPORTED_NETWORKS,
)
from .services.mock_data import (
    get_mock_trending_pools,
)
from .services.response_builder import (
    build_market_insights_response,
    build_error_response,
)


class MarketInsightsAgent:
    """Agent that retrieves market insights using hardcoded mock data for demo purposes."""

    def __init__(self):
        self._user_id = DEFAULT_USER_ID

    def _parse_query(self, query: str) -> dict:
        """Parse query to extract network for trending tokens."""
        query_lower = query.lower()
        
        result = {
            "network": None,
        }
        
        # Extract network
        for network in SUPPORTED_NETWORKS:
            if network in query_lower or (network == "eth" and "ethereum" in query_lower):
                result["network"] = network
                break
        
        return result

    async def invoke(self, query: str, session_id: str) -> str:
        """
        Invoke the market insights agent with a query.
        Only handles trending tokens/pools queries.

        Args:
            query: User query (e.g., "Show trending tokens" or "Show trending pools on Polygon")
            session_id: Session ID

        Returns:
            JSON string with trending pools data
        """
        print(f"📊 Market Insights Agent received query: {query}")

        try:
            # Parse query to get network
            parsed = self._parse_query(query)
            network = parsed.get("network")
            
            print(f"📋 Parsed: network={network}")
            
            # Always fetch trending tokens
            print(f"🔍 Fetching trending tokens...")
            trending_data = get_mock_trending_pools(network)
            
            if not trending_data or not trending_data.get("data"):
                return build_error_response(
                    f"No trending tokens found. "
                    f"Try: 'Show trending tokens' or 'Show trending tokens on Polygon'"
                )
            
            # Build response with only trending tokens data
            response = build_market_insights_response(
                network=network,
                token_address=None,
                pool_address=None,
                pool_data=None,
                token_data=None,
                trending_data=trending_data,
            )
            
            print(f"✅ Market Insights Agent response built with {len(trending_data.get('data', []))} trending tokens")
            return response

        except Exception as e:
            print(f"❌ Error in Market Insights Agent: {e}")
            import traceback
            traceback.print_exc()
            return build_error_response(str(e))

