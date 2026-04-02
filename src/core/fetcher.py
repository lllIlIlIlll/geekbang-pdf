"""Page HTML fetching module."""

import re
import requests
from urllib.parse import urljoin, urlparse

from .exceptions import URLInvalidError, FetchError


def parse_cookie_string(cookie_str):
    """Parse a cookie string into a dictionary.

    Args:
        cookie_str: Cookie string in format "name=value; name=value"

    Returns:
        dict: Cookie dictionary
    """
    if not cookie_str:
        return {}

    cookies = {}
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            name, value = part.split("=", 1)
            cookies[name.strip()] = value.strip()
    return cookies


def validate_url(url):
    """Validate that the URL is a valid geekbang URL.

    Args:
        url: URL to validate

    Returns:
        bool: True if valid

    Raises:
        URLInvalidError: If URL is invalid
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise URLInvalidError(f"Invalid URL format: {url}")

    if "geekbang" not in parsed.netloc:
        raise URLInvalidError(f"URL must be from geekbang.org: {url}")

    return True


def fetch_page(url, cookies=None):
    """Fetch page HTML content.

    Args:
        url: URL to fetch
        cookies: Optional cookie string for authenticated requests

    Returns:
        tuple: (html_content, base_url)

    Raises:
        URLInvalidError: If URL is invalid
        FetchError: If fetch fails
    """
    validate_url(url)

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    try:
        # Convert cookie string to dict if needed
        if isinstance(cookies, str):
            cookies = parse_cookie_string(cookies)

        response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"

        # Determine base URL for resolving relative paths
        base_url = response.url

        return response.text, base_url

    except requests.exceptions.RequestException as e:
        raise FetchError(f"Failed to fetch page: {str(e)}")


def get_page_title(html, base_url):
    """Extract page title from HTML.

    Args:
        html: HTML content
        base_url: Base URL for resolving relative links

    Returns:
        str: Page title
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.find("title")

    if title_tag:
        return title_tag.get_text(strip=True)

    # Try og:title
    og_title = soup.find("meta", property="og:title")
    if og_title:
        return og_title.get("content", "")

    return "Untitled"
