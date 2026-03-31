"""Custom exceptions for GeekBang PDF Saver."""


class GeekBangError(Exception):
    """Base exception for GeekBang PDF Saver."""
    pass


class URLInvalidError(GeekBangError):
    """Raised when the provided URL is invalid."""
    pass


class FetchError(GeekBangError):
    """Raised when page fetching fails."""
    pass


class AuthError(GeekBangError):
    """Raised when authentication fails."""
    pass


class ConversionError(GeekBangError):
    """Raised when PDF conversion fails."""
    pass


class ConfigError(GeekBangError):
    """Raised when config operations fail."""
    pass
