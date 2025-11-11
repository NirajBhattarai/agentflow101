"""
Unit tests for token pair extraction in parallel liquidity agent.
"""

from agents.parallel_liquidity.services.query_parser import extract_token_pair


class TestTokenPairExtraction:
    """Test cases for token pair extraction."""

    def test_extract_token_pair_slash_format(self):
        """Test extracting token pair in ETH/USDT format."""
        query = "Get liquidity for ETH/USDT"
        token_pair = extract_token_pair(query)
        assert token_pair == "ETH/USDT"

    def test_extract_token_pair_hbar_usdc(self):
        """Test extracting HBAR/USDC pair."""
        query = "Find liquidity pools for HBAR/USDC"
        token_pair = extract_token_pair(query)
        assert token_pair == "HBAR/USDC"

    def test_extract_token_pair_matic_usdc(self):
        """Test extracting MATIC/USDC pair."""
        query = "Show me liquidity for MATIC/USDC"
        token_pair = extract_token_pair(query)
        assert token_pair == "MATIC/USDC"

    def test_extract_token_pair_with_pair_keyword(self):
        """Test extracting token pair with 'pair:' keyword."""
        query = "Get liquidity pair: ETH/USDT"
        token_pair = extract_token_pair(query)
        assert token_pair == "ETH/USDT"

    def test_extract_token_pair_with_for_keyword(self):
        """Test extracting token pair with 'for' keyword."""
        query = "Get liquidity for USDC/USDT"
        token_pair = extract_token_pair(query)
        assert token_pair == "USDC/USDT"

    def test_extract_token_pair_case_insensitive(self):
        """Test that extraction is case insensitive."""
        query = "get liquidity for eth/usdt"
        token_pair = extract_token_pair(query)
        assert token_pair == "ETH/USDT"

    def test_extract_token_pair_none_when_not_found(self):
        """Test that None is returned when no token pair found."""
        query = "Get liquidity information"
        token_pair = extract_token_pair(query)
        assert token_pair is None

    def test_extract_token_pair_empty_query(self):
        """Test that None is returned for empty query."""
        token_pair = extract_token_pair("")
        assert token_pair is None
