from typing import Any


class JwtServiceError(Exception):
    """Base exception for JWT service errors."""
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class TokenExpiredError(JwtServiceError):
    """Token has expired."""
    pass


class TokenRevokedError(JwtServiceError):
    """Token has been revoked."""
    pass


class TokenFamilyRevokedError(JwtServiceError):
    """Token family has been revoked (replay attack detected)."""
    pass


class InvalidTokenError(JwtServiceError):
    """Token is malformed or signature is invalid."""
    pass


class TokenTypeMismatchError(JwtServiceError):
    """Token type doesn't match expected type."""
    pass
