class HttpError(Exception):
    """Base class for HTTP client errors."""
    pass

class MaxRetriesExceededError(HttpError):
    """Raised when connection retries reach maximum limit."""
    pass

class SecurityViolationError(HttpError):
    """Raised when request violates transport security invariant."""
    pass
