"""
Unit tests for result combination in parallel liquidity agent.
"""

import json
from agents.parallel_liquidity.agents.parallel_liquidity_executor import (
    ParallelLiquidityAgent,
)


class TestResultCombination:
    """Test cases for combining results from multiple chains."""

    def test_combine_results_both_chains(
        self, mock_hedera_liquidity_result, mock_polygon_liquidity_result
    ):
        """Test combining results from both chains."""
        agent = ParallelLiquidityAgent()
        token_pair = "ETH/USDT"
        result = agent._combine_results(
            token_pair, mock_hedera_liquidity_result, mock_polygon_liquidity_result
        )
        data = json.loads(result)

        assert data["type"] == "parallel_liquidity"
        assert data["token_pair"] == "ETH/USDT"
        assert len(data["hedera_pairs"]) == 1
        assert len(data["polygon_pairs"]) == 1
        assert len(data["all_pairs"]) == 2
        assert data["chains"]["hedera"]["total_pools"] == 1
        assert data["chains"]["polygon"]["total_pools"] == 1

    def test_combine_results_hedera_only(self, mock_hedera_liquidity_result):
        """Test combining results with only Hedera data."""
        agent = ParallelLiquidityAgent()
        token_pair = "HBAR/USDC"
        result = agent._combine_results(token_pair, mock_hedera_liquidity_result, None)
        data = json.loads(result)

        assert data["type"] == "parallel_liquidity"
        assert data["token_pair"] == "HBAR/USDC"
        assert len(data["hedera_pairs"]) == 1
        assert len(data["polygon_pairs"]) == 0
        assert len(data["all_pairs"]) == 1

    def test_combine_results_polygon_only(self, mock_polygon_liquidity_result):
        """Test combining results with only Polygon data."""
        agent = ParallelLiquidityAgent()
        token_pair = "MATIC/USDC"
        result = agent._combine_results(token_pair, None, mock_polygon_liquidity_result)
        data = json.loads(result)

        assert data["type"] == "parallel_liquidity"
        assert data["token_pair"] == "MATIC/USDC"
        assert len(data["hedera_pairs"]) == 0
        assert len(data["polygon_pairs"]) == 1
        assert len(data["all_pairs"]) == 1

    def test_combine_results_no_data(self):
        """Test combining results with no data."""
        agent = ParallelLiquidityAgent()
        token_pair = "ETH/USDT"
        result = agent._combine_results(token_pair, None, None)
        data = json.loads(result)

        assert data["type"] == "parallel_liquidity"
        assert data["token_pair"] == "ETH/USDT"
        assert len(data["hedera_pairs"]) == 0
        assert len(data["polygon_pairs"]) == 0
        assert len(data["all_pairs"]) == 0

    def test_combine_results_string_inputs(self, mock_hedera_liquidity_result):
        """Test combining results when inputs are JSON strings."""
        agent = ParallelLiquidityAgent()
        token_pair = "ETH/USDT"
        hedera_json = json.dumps(mock_hedera_liquidity_result)
        result = agent._combine_results(token_pair, hedera_json, None)
        data = json.loads(result)

        assert data["type"] == "parallel_liquidity"
        assert len(data["hedera_pairs"]) == 1

    def test_combine_results_liquidity_pair_structure(
        self, mock_hedera_liquidity_result
    ):
        """Test that combined results have correct LiquidityPair structure."""
        agent = ParallelLiquidityAgent()
        token_pair = "ETH/USDT"
        result = agent._combine_results(token_pair, mock_hedera_liquidity_result, None)
        data = json.loads(result)

        hedera_pair = data["hedera_pairs"][0]
        assert hedera_pair["base"] == "ETH"
        assert hedera_pair["quote"] == "USDT"
        assert hedera_pair["chain"] == "hedera"
        assert hedera_pair["dex"] == "SaucerSwap"
        assert "pool_address" in hedera_pair
        assert "tvl_usd" in hedera_pair
        assert "reserve_base" in hedera_pair
        assert "reserve_quote" in hedera_pair
        assert "fee_bps" in hedera_pair


class TestTVLParsing:
    """Test cases for TVL parsing."""

    def test_parse_tvl_dollar_format(self):
        """Test parsing TVL in $1,200,000 format."""
        agent = ParallelLiquidityAgent()
        assert agent._parse_tvl("$1,200,000") == 1200000.0

    def test_parse_tvl_no_dollar(self):
        """Test parsing TVL without dollar sign."""
        agent = ParallelLiquidityAgent()
        assert agent._parse_tvl("500000") == 500000.0

    def test_parse_tvl_numeric(self):
        """Test parsing TVL as numeric value."""
        agent = ParallelLiquidityAgent()
        assert agent._parse_tvl(1000000) == 1000000.0

    def test_parse_tvl_invalid(self):
        """Test parsing invalid TVL string."""
        agent = ParallelLiquidityAgent()
        assert agent._parse_tvl("invalid") == 0.0

    def test_parse_tvl_empty(self):
        """Test parsing empty TVL string."""
        agent = ParallelLiquidityAgent()
        assert agent._parse_tvl("") == 0.0

    def test_parse_tvl_none(self):
        """Test parsing None TVL."""
        agent = ParallelLiquidityAgent()
        assert agent._parse_tvl(None) == 0.0
