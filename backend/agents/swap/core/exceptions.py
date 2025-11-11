"""
Custom exceptions for Swap Agent.

Domain-specific exceptions for better error handling.
"""


class SwapAgentError(Exception):
    """Base exception for Swap Agent errors."""

    pass


class InvalidSwapParametersError(SwapAgentError):
    """Raised when swap parameters are invalid."""

    def __init__(self, reason: str = "", details: dict = None):
        self.reason = reason
        self.details = details or {}
        message = "Invalid swap parameters"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class ChainNotSupportedError(SwapAgentError):
    """Raised when an unsupported chain is requested."""

    def __init__(self, chain: str):
        self.chain = chain
        super().__init__(f"Chain not supported: {chain}")


class SwapExecutionError(SwapAgentError):
    """Raised when swap execution fails."""

    def __init__(self, chain: str, reason: str = ""):
        self.chain = chain
        self.reason = reason
        message = f"Failed to execute swap on {chain}"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class ValidationError(SwapAgentError):
    """Raised when response validation fails."""

    def __init__(self, message: str, details: dict = None):
        self.details = details or {}
        super().__init__(message)


class InsufficientBalanceError(SwapAgentError):
    """Raised when account has insufficient balance."""

    def __init__(self, token_symbol: str, required: str, available: str):
        self.token_symbol = token_symbol
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient {token_symbol} balance: required {required}, available {available}"
        )
