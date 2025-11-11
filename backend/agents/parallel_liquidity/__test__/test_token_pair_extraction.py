"""
Unit tests for token pair extraction in parallel liquidity agent.
"""

from agents.parallel_liquidity.agents.parallel_liquidity_executor import (
    ParallelLiquidityAgent,
)


class TestTokenPairExtraction:
    """Test cases for token pair extraction."""

    def test_extract_token_pair_slash_format(self):
        """Test extracting token pair in ETH/USDT format."""
        agent = ParallelLiquidityAgent()
        query = "Get liquidity for ETH/USDT"
        token_pair = agent._extract_token_pair(query)
        assert token_pair == "ETH/USDT"

    def test_extract_token_pair_hbar_usdc(self):
        """Test extracting HBAR/USDC pair."""
        agent = ParallelLiquidityAgent()
        query = "Find liquidity pools for HBAR/USDC"
        token_pair = agent._extract_token_pair(query)
        assert token_pair == "HBAR/USDC"

    def test_extract_token_pair_matic_usdc(self):
        """Test extracting MATIC/USDC pair."""
        agent = ParallelLiquidityAgent()
        query = "Show me liquidity for MATIC/USDC"
        token_pair = agent._extract_token_pair(query)
        assert token_pair == "MATIC/USDC"

    def test_extract_token_pair_with_pair_keyword(self):
        """Test extracting token pair with 'pair:' keyword."""
        agent = ParallelLiquidityAgent()
        query = "Get liquidity pair: ETH/USDT"
        token_pair = agent._extract_token_pair(query)
        assert token_pair == "ETH/USDT"

    def test_extract_token_pair_with_for_keyword(self):
        """Test extracting token pair with 'for' keyword."""
        agent = ParallelLiquidityAgent()
        query = "Get liquidity for USDC/USDT"
        token_pair = agent._extract_token_pair(query)
        assert token_pair == "USDC/USDT"

    def test_extract_token_pair_case_insensitive(self):
        """Test that extraction is case insensitive."""
        agent = ParallelLiquidityAgent()
        query = "get liquidity for eth/usdt"
        token_pair = agent._extract_token_pair(query)
        assert token_pair == "ETH/USDT"

    def test_extract_token_pair_none_when_not_found(self):
        """Test that None is returned when no token pair found."""
        agent = ParallelLiquidityAgent()
        query = "Get liquidity information"
        token_pair = agent._extract_token_pair(query)
        assert token_pair is None

    def test_extract_token_pair_empty_query(self):
        """Test that None is returned for empty query."""
        agent = ParallelLiquidityAgent()
        token_pair = agent._extract_token_pair("")
        assert token_pair is None
