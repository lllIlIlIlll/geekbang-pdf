"""Tests for exception classes."""

import pytest

from src.core.exceptions import (
    AuthError,
    ConfigError,
    ConversionError,
    FetchError,
    GeekBangError,
    URLInvalidError,
)


class TestExceptionCodes:
    """Tests for exception error codes."""

    def test_geekbang_error_code(self):
        """GeekBangError should have UNKNOWN code."""
        error = GeekBangError("test error")
        assert error.code == "UNKNOWN"
        assert "[UNKNOWN]" in str(error)

    def test_url_invalid_error_code(self):
        """URLInvalidError should have correct code."""
        error = URLInvalidError("Invalid URL")
        assert error.code == "URL"
        assert "[URL]" in str(error)

    def test_fetch_error_code(self):
        """FetchError should have correct code."""
        error = FetchError("Fetch failed")
        assert error.code == "FETCH"
        assert "[FETCH]" in str(error)

    def test_auth_error_code(self):
        """AuthError should have correct code."""
        error = AuthError("Auth failed")
        assert error.code == "AUTH"
        assert "[AUTH]" in str(error)

    def test_conversion_error_code(self):
        """ConversionError should have correct code."""
        error = ConversionError("Conversion failed")
        assert error.code == "CONV"
        assert "[CONV]" in str(error)

    def test_config_error_code(self):
        """ConfigError should have correct code."""
        error = ConfigError("Config failed")
        assert error.code == "CONFIG"
        assert "[CONFIG]" in str(error)


class TestExceptionInheritance:
    """Tests for exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_geekbang_error(self):
        """All custom exceptions should inherit from GeekBangError."""
        assert issubclass(URLInvalidError, GeekBangError)
        assert issubclass(FetchError, GeekBangError)
        assert issubclass(AuthError, GeekBangError)
        assert issubclass(ConversionError, GeekBangError)
        assert issubclass(ConfigError, GeekBangError)

    def test_exception_messages(self):
        """Exception messages should be preserved."""
        msg = "This is a test error message"
        error = GeekBangError(msg)
        assert msg in str(error)
