"""
Custom exceptions for Parallel Liquidity Agent.
"""


class ParallelLiquidityAgentError(Exception):
    """Base exception for Parallel Liquidity Agent errors."""

    pass


class TokenPairExtractionError(ParallelLiquidityAgentError):
    """Raised when token pair cannot be extracted from query."""

    pass


class ResultCombinationError(ParallelLiquidityAgentError):
    """Raised when combining results from chains fails."""

    pass


class ValidationError(ParallelLiquidityAgentError):
    """Raised when response data fails validation."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details if details is not None else {}
