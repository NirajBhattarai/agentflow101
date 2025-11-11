"""
Custom exceptions for Swap Router Agent.
"""


class SwapRouterError(Exception):
    """Base exception for swap router errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}


class InsufficientLiquidityError(SwapRouterError):
    """Raised when there's insufficient liquidity for the swap."""

    pass


class PriceImpactTooHighError(SwapRouterError):
    """Raised when price impact exceeds threshold."""

    pass


class ChainNotSupportedError(SwapRouterError):
    """Raised when chain is not supported."""

    pass


class InvalidSwapAmountError(SwapRouterError):
    """Raised when swap amount is invalid."""

    pass
