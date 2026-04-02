"""GeekBang PDF Saver - Save geekbang.org course pages as PDF."""

from .core import (
    GeekBangError,
    URLInvalidError,
    FetchError,
    AuthError,
    ConversionError,
    ConfigError,
)

__version__ = "1.0.0"

__all__ = [
    "GeekBangError",
    "URLInvalidError",
    "FetchError",
    "AuthError",
    "ConversionError",
    "ConfigError",
]
