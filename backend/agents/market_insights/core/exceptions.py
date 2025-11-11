"""
Custom exceptions for Market Insights Agent.
"""


class MarketInsightsError(Exception):
    """Base exception for Market Insights Agent errors."""

    pass


class CoinGeckoAPIError(MarketInsightsError):
    """Exception raised when CoinGecko API call fails."""

    pass


class NetworkNotSupportedError(MarketInsightsError):
    """Exception raised when network is not supported."""

    pass


class InvalidTokenAddressError(MarketInsightsError):
    """Exception raised when token address is invalid."""

    pass

