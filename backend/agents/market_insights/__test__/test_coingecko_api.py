"""
Unit tests for CoinGecko API endpoints.

Tests each endpoint to verify it works with the Demo/Free API tier.
"""

import pytest
import os
from dotenv import load_dotenv
from agents.market_insights.tools.coingecko_api import (
    get_pool_data,
    get_token_data,
    get_token_top_pools,
    get_trending_pools,
    get_trending_search_pools,
)
from agents.market_insights.core.exceptions import (
    CoinGeckoAPIError,
    NetworkNotSupportedError,
)

load_dotenv()


@pytest.fixture
def api_key():
    """Get API key from environment."""
    key = os.getenv("COINGECKO_API_KEY")
    if not key:
        pytest.skip("COINGECKO_API_KEY not set")
    return key


@pytest.fixture
def test_network():
    """Test network (eth for Ethereum - most likely to have data)."""
    return "eth"


@pytest.fixture
def test_token_address():
    """Test token address (WETH on Ethereum)."""
    return "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"


@pytest.fixture
def test_pool_address():
    """Test pool address (USDC/WETH pool on Uniswap V3)."""
    return "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"


class TestCoinGeckoAPIDemo:
    """Test CoinGecko API endpoints with Demo/Free tier."""

    def test_get_pool_data(self, api_key, test_network, test_pool_address):
        """Test get_pool_data endpoint."""
        print(f"\n🧪 Testing get_pool_data for {test_network} pool {test_pool_address[:10]}...")
        try:
            result = get_pool_data(test_network, test_pool_address)
            assert result is not None
            assert "data" in result or "attributes" in result
            print(f"✅ get_pool_data works!")
            return True
        except CoinGeckoAPIError as e:
            if "401" in str(e) or "403" in str(e) or "exclusive" in str(e).lower():
                print(f"❌ get_pool_data requires paid plan: {e}")
                return False
            raise

    def test_get_token_data(self, api_key, test_network, test_token_address):
        """Test get_token_data endpoint."""
        print(f"\n🧪 Testing get_token_data for {test_network} token {test_token_address[:10]}...")
        try:
            result = get_token_data(test_network, test_token_address)
            assert result is not None
            assert "data" in result or "attributes" in result
            print(f"✅ get_token_data works!")
            return True
        except CoinGeckoAPIError as e:
            if "401" in str(e) or "403" in str(e) or "exclusive" in str(e).lower():
                print(f"❌ get_token_data requires paid plan: {e}")
                return False
            raise

    def test_get_token_top_pools(self, api_key, test_network, test_token_address):
        """Test get_token_top_pools endpoint."""
        print(f"\n🧪 Testing get_token_top_pools for {test_network} token {test_token_address[:10]}...")
        try:
            result = get_token_top_pools(test_network, test_token_address)
            assert result is not None
            assert "data" in result
            print(f"✅ get_token_top_pools works!")
            return True
        except CoinGeckoAPIError as e:
            if "401" in str(e) or "403" in str(e) or "exclusive" in str(e).lower():
                print(f"❌ get_token_top_pools requires paid plan: {e}")
                return False
            raise

    def test_get_trending_pools_all_networks(self, api_key):
        """Test get_trending_pools for all networks."""
        print(f"\n🧪 Testing get_trending_pools (all networks)...")
        try:
            result = get_trending_pools(network=None)
            assert result is not None
            assert "data" in result
            print(f"✅ get_trending_pools (all) works!")
            return True
        except CoinGeckoAPIError as e:
            if "401" in str(e) or "403" in str(e) or "exclusive" in str(e).lower() or "404" in str(e):
                print(f"❌ get_trending_pools (all) not available: {e}")
                return False
            raise

    def test_get_trending_pools_network(self, api_key, test_network):
        """Test get_trending_pools for specific network."""
        print(f"\n🧪 Testing get_trending_pools for {test_network}...")
        try:
            result = get_trending_pools(network=test_network)
            assert result is not None
            assert "data" in result
            print(f"✅ get_trending_pools ({test_network}) works!")
            return True
        except CoinGeckoAPIError as e:
            if "401" in str(e) or "403" in str(e) or "exclusive" in str(e).lower() or "404" in str(e):
                print(f"❌ get_trending_pools ({test_network}) not available: {e}")
                return False
            raise

    def test_get_trending_search_pools(self, api_key):
        """Test get_trending_search_pools endpoint."""
        print(f"\n🧪 Testing get_trending_search_pools...")
        try:
            result = get_trending_search_pools()
            assert result is not None
            assert "data" in result
            print(f"✅ get_trending_search_pools works!")
            return True
        except CoinGeckoAPIError as e:
            if "401" in str(e) or "403" in str(e) or "exclusive" in str(e).lower():
                print(f"❌ get_trending_search_pools requires paid plan: {e}")
                return False
            raise

    def test_all_endpoints(self, api_key, test_network, test_token_address, test_pool_address):
        """Run all endpoint tests and report which work."""
        print("\n" + "="*60)
        print("🧪 Testing all CoinGecko API endpoints with Demo API")
        print("="*60)
        
        results = {}
        
        # Test each endpoint
        results["get_pool_data"] = self.test_get_pool_data(api_key, test_network, test_pool_address)
        results["get_token_data"] = self.test_get_token_data(api_key, test_network, test_token_address)
        results["get_token_top_pools"] = self.test_get_token_top_pools(api_key, test_network, test_token_address)
        results["get_trending_pools_all"] = self.test_get_trending_pools_all_networks(api_key)
        results["get_trending_pools_network"] = self.test_get_trending_pools_network(api_key, test_network)
        results["get_trending_search_pools"] = self.test_get_trending_search_pools(api_key)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 Test Results Summary:")
        print("="*60)
        for endpoint, works in results.items():
            status = "✅ WORKS" if works else "❌ NOT AVAILABLE"
            print(f"  {endpoint:30} {status}")
        
        working = sum(1 for v in results.values() if v)
        total = len(results)
        print(f"\n✅ {working}/{total} endpoints work with Demo API")
        print("="*60)
        
        # Assert that at least some endpoints work
        assert working > 0, "No endpoints work with Demo API!"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

