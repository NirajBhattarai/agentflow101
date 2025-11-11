"""
Custom exceptions for Multi-Chain Liquidity Agent.
"""


class MultiChainLiquidityError(Exception):
    """Base exception for multi-chain liquidity errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}


class TokenPairNotFoundError(MultiChainLiquidityError):
    """Raised when token pair cannot be extracted from query."""

    pass


class ValidationError(MultiChainLiquidityError):
    """Raised when response validation fails."""

    pass
