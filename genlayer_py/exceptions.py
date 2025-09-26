from typing import Any, Optional


class GenLayerError(Exception):
    """Base exception class for GenLayer SDK errors.

    This exception can carry additional context information through an optional
    payload dictionary, useful for debugging and error handling.

    Args:
        message: Human-readable error description.
        payload: Optional dictionary containing additional error context,
                 such as transaction details, error codes, or debug information.

    Attributes:
        payload: Dictionary of additional error context (None if not provided).

    Example:
        >>> raise GenLayerError(
        ...     "Transaction failed",
        ...     {"tx_hash": "0x123...", "reason": "insufficient funds"}
        ... )
    """

    def __init__(self, message: str, payload: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.payload = payload
