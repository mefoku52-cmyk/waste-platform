from typing import Any


class JwtServiceError(Exception):
    """Base exception for JWT service errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class TokenExpiredError(JwtServiceError):
    """Token has expired."""


class TokenRevokedError(JwtServiceError):
    """Token has been revoked."""


class TokenFamilyRevokedError(JwtServiceError):
    """Token family has been revoked (replay attack detected)."""


class TokenUserRevokedError(JwtServiceError):
    """All user sessions issued before cutoff have been revoked."""


class InvalidTokenError(JwtServiceError):
    """Token is malformed or signature is invalid."""


class TokenTypeMismatchError(JwtServiceError):
    """Token type doesn't match expected type."""
