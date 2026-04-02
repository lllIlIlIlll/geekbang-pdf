"""Constants for GeekBang PDF Saver - eliminates magic numbers."""

from typing import Final


class ConversionConstants:
    """Timeouts and wait durations in milliseconds."""

    # Navigation and page load
    NAVIGATION_TIMEOUT_MS: Final[int] = 60000  # converter.py:50, main.py:134
    PAGE_LOAD_WAIT_MS: Final[int] = 8000  # converter.py:51

    # Short waits (1 second)
    SHORT_WAIT_MS: Final[int] = 1000  # converter.py:74,138,333

    # Medium waits (2 seconds)
    MEDIUM_WAIT_MS: Final[int] = 2000  # converter.py:279,293,391

    # Extra login timeout
    LOGIN_TIMEOUT_EXTRA_MS: Final[int] = 30000  # main.py:194


class LoginConstants:
    """Login-related timing constants in seconds."""

    MAX_LOGIN_WAIT_SECONDS: Final[int] = 120  # main.py:161
    LOGIN_POLL_INTERVAL_SECONDS: Final[int] = 2  # main.py:162


class ViewportConstants:
    """Viewport dimensions."""

    VIEWPORT_WIDTH: Final[int] = 1920  # Multiple locations
    MIN_VIEWPORT_HEIGHT: Final[int] = 4000  # converter.py:291
    DEFAULT_CONTENT_HEIGHT: Final[int] = 25000  # converter.py:394
