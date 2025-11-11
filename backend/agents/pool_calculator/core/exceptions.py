"""
Custom exceptions for Pool Calculator Agent.
"""


class PoolCalculatorError(Exception):
    """Base exception for pool calculator errors."""

    pass


class InvalidPoolDataError(PoolCalculatorError):
    """Raised when pool data is invalid or missing required fields."""

    pass


class CalculationError(PoolCalculatorError):
    """Raised when a calculation fails."""

    pass


class InsufficientDataError(PoolCalculatorError):
    """Raised when required data for calculation is missing."""

    pass

