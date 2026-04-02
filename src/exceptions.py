"""Custom exceptions for GeekBang PDF Saver with error codes."""


class GeekBangError(Exception):
    """Base exception for GeekBang PDF Saver."""

    CODE = "UNKNOWN"
    DEFAULT_MESSAGE = "An unknown error occurred"

    def __init__(self, message: str = None, code: str = None):
        self.message = message or self.DEFAULT_MESSAGE
        self.code = code or self.CODE
        super().__init__(f"[{self.code}] {self.message}")


class URLInvalidError(GeekBangError):
    """Raised when the provided URL is invalid."""

    CODE = "URL"
    DEFAULT_MESSAGE = "Invalid URL provided"


class FetchError(GeekBangError):
    """Raised when page fetching fails."""

    CODE = "FETCH"
    DEFAULT_MESSAGE = "Failed to fetch page content"


class AuthError(GeekBangError):
    """Raised when authentication fails."""

    CODE = "AUTH"
    DEFAULT_MESSAGE = "Authentication failed"

    # Specific auth errors
    INVALID_CREDENTIALS = ("Invalid credentials", "AUTH_001")
    SESSION_EXPIRED = ("Session has expired", "AUTH_002")
    LOGIN_TIMEOUT = ("Login timeout", "AUTH_003")


class ConversionError(GeekBangError):
    """Raised when PDF conversion fails."""

    CODE = "CONV"
    DEFAULT_MESSAGE = "Failed to convert page to PDF"

    # Specific conversion errors
    NAVIGATION_FAILED = ("Page navigation failed", "CONV_001")
    CONTENT_LOAD_TIMEOUT = ("Content load timeout", "CONV_002")


class ConfigError(GeekBangError):
    """Raised when config operations fail."""

    CODE = "CONFIG"
    DEFAULT_MESSAGE = "Configuration error"

    # Specific config errors
    PATH_TRAVERSAL_BLOCKED = ("Path traversal attempt blocked", "CONFIG_001")
    COOKIE_ENCRYPTION_FAILED = ("Failed to encrypt cookie", "CONFIG_002")
    COOKIE_DECRYPTION_FAILED = ("Failed to decrypt cookie", "CONFIG_003")
