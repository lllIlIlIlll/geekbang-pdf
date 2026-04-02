"""Core modules for GeekBang PDF Saver."""

from .exceptions import (
    GeekBangError,
    URLInvalidError,
    FetchError,
    AuthError,
    ConversionError,
    ConfigError,
)
from .auth import login, login_with_cookie, get_cookies_from_existing_chrome
from .converter import (
    convert_with_context,
    convert_with_cookie,
    convert_chrome_page_to_pdf,
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
    "login_with_cookie",
    "get_cookies_from_existing_chrome",
    # Converter
    "convert_with_context",
    "convert_with_cookie",
    "convert_chrome_page_to_pdf",
    # Fetcher
    "fetch_page",
    "validate_url",
    "parse_cookie_string",
    # Parser
    "process_html",
    "extract_article_content",
]
