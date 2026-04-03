"""Core modules for GeekBang PDF Saver."""

from .exceptions import (
    GeekBangError,
    URLInvalidError,
    FetchError,
    AuthError,
    ConversionError,
    ConfigError,
)
from .auth import login
from .converter import (
    convert_with_context,
)
from .fetcher import fetch_page, validate_url, parse_cookie_string
from .parser import process_html, extract_article_content

__all__ = [
    # Exceptions
    "GeekBangError",
    "URLInvalidError",
    "FetchError",
    "AuthError",
    "ConversionError",
    "ConfigError",
    # Auth
    "login",
    # Converter
    "convert_with_context",
    # Fetcher
    "fetch_page",
    "validate_url",
    "parse_cookie_string",
    # Parser
    "process_html",
    "extract_article_content",
]
