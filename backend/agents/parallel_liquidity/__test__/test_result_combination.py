"""
Unit tests for result combination in parallel liquidity agent.
"""

import json


class TestResultCombination:
    """Test cases for combining results from multiple chains."""

    def test_combine_results_both_chains(
        self, mock_hedera_liquidity_result, mock_polygon_liquidity_result
    ):
        """Test combining results from both chains."""
        from agents.parallel_liquidity.services.result_combiner import combine_results

        token_pair = "ETH/USDT"
        combined_data = combine_results(
            token_pair, mock_hedera_liquidity_result, mock_polygon_liquidity_result
        )
        result = json.dumps(combined_data, indent=2)
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
        from agents.parallel_liquidity.services.result_combiner import combine_results

        token_pair = "HBAR/USDC"
        combined_data = combine_results(token_pair, mock_hedera_liquidity_result, None)
        data = combined_data

        assert data["type"] == "parallel_liquidity"
        assert data["token_pair"] == "HBAR/USDC"
        assert len(data["hedera_pairs"]) == 1
        assert len(data["polygon_pairs"]) == 0
        assert len(data["all_pairs"]) == 1

    def test_combine_results_polygon_only(self, mock_polygon_liquidity_result):
        """Test combining results with only Polygon data."""
        from agents.parallel_liquidity.services.result_combiner import combine_results

        token_pair = "MATIC/USDC"
        combined_data = combine_results(token_pair, None, mock_polygon_liquidity_result)
        data = combined_data

        assert data["type"] == "parallel_liquidity"
        assert data["token_pair"] == "MATIC/USDC"
        assert len(data["hedera_pairs"]) == 0
        assert len(data["polygon_pairs"]) == 1
        assert len(data["all_pairs"]) == 1

    def test_combine_results_no_data(self):
        """Test combining results with no data."""
        from agents.parallel_liquidity.services.result_combiner import combine_results

        token_pair = "ETH/USDT"
        data = combine_results(token_pair, None, None)

        assert data["type"] == "parallel_liquidity"
        assert data["token_pair"] == "ETH/USDT"
        assert len(data["hedera_pairs"]) == 0
        assert len(data["polygon_pairs"]) == 0
        assert len(data["all_pairs"]) == 0

    def test_combine_results_string_inputs(self, mock_hedera_liquidity_result):
        """Test combining results when inputs are JSON strings."""
        from agents.parallel_liquidity.services.result_combiner import combine_results

        token_pair = "ETH/USDT"
        hedera_json = json.dumps(mock_hedera_liquidity_result)
        data = combine_results(token_pair, hedera_json, None)

        assert data["type"] == "parallel_liquidity"
        assert len(data["hedera_pairs"]) == 1

    def test_combine_results_liquidity_pair_structure(
        self, mock_hedera_liquidity_result
    ):
        """Test that combined results have correct LiquidityPair structure."""
        from agents.parallel_liquidity.services.result_combiner import combine_results

        token_pair = "ETH/USDT"
        data = combine_results(token_pair, mock_hedera_liquidity_result, None)

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
        from agents.parallel_liquidity.services.result_combiner import parse_tvl

        assert parse_tvl("$1,200,000") == 1200000.0

    def test_parse_tvl_no_dollar(self):
        """Test parsing TVL without dollar sign."""
        from agents.parallel_liquidity.services.result_combiner import parse_tvl

        assert parse_tvl("500000") == 500000.0

    def test_parse_tvl_numeric(self):
        """Test parsing TVL as numeric value."""
        from agents.parallel_liquidity.services.result_combiner import parse_tvl

        assert parse_tvl(1000000) == 1000000.0

    def test_parse_tvl_invalid(self):
        """Test parsing invalid TVL string."""
        from agents.parallel_liquidity.services.result_combiner import parse_tvl

        assert parse_tvl("invalid") == 0.0

    def test_parse_tvl_empty(self):
        """Test parsing empty TVL string."""
        from agents.parallel_liquidity.services.result_combiner import parse_tvl

        assert parse_tvl("") == 0.0

    def test_parse_tvl_none(self):
        """Test parsing None TVL."""
        from agents.parallel_liquidity.services.result_combiner import parse_tvl

        assert parse_tvl(None) == 0.0
