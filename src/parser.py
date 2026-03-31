"""HTML parsing and resource processing module."""

import os
import re
import hashlib
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .exceptions import FetchError


def make_absolute(url, base_url):
    """Convert relative URL to absolute URL.

    Args:
        url: URL (possibly relative)
        base_url: Base URL for resolution

    Returns:
        str: Absolute URL
    """
    if not url:
        return url
    if url.startswith(("http://", "https://", "//")):
        if url.startswith("//"):
            return "https:" + url
        return url
    return urljoin(base_url, url)


def download_image(url, timeout=10):
    """Download an image and return its path.

    Args:
        url: Image URL
        timeout: Request timeout in seconds

    Returns:
        str: Path to downloaded image (relative)
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        # Determine file extension from content type or URL
        content_type = response.headers.get("Content-Type", "")
        ext = ".jpg"
        if "png" in content_type:
            ext = ".png"
        elif "gif" in content_type:
            ext = ".gif"
        elif "webp" in content_type:
            ext = ".webp"

        # Generate unique filename
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        filename = f"img_{url_hash}{ext}"

        # Save to images directory
        img_dir = Path("images")
        img_dir.mkdir(exist_ok=True)
        filepath = img_dir / filename

        with open(filepath, "wb") as f:
            f.write(response.content)

        return str(filepath)

    except Exception:
        return None


def process_html(html_content, base_url, download_images=True):
    """Process HTML content for PDF conversion.

    Args:
        html_content: Raw HTML string
        base_url: Base URL for resolving relative paths
        download_images: Whether to download images locally

    Returns:
        str: Processed HTML content
    """
    soup = BeautifulSoup(html_content, "lxml")

    # Update base tag to ensure proper relative URL resolution
    base_tag = soup.find("base")
    if base_tag:
        base_tag["href"] = base_url
    else:
        new_base = soup.new_tag("base", href=base_url)
        if soup.head:
            soup.head.insert(0, new_base)
        else:
            head = soup.new_tag("head")
            head.append(new_base)
            soup.html.insert(0, head)

    # Process images
    if download_images:
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src:
                abs_url = make_absolute(src, base_url)
                local_path = download_image(abs_url)
                if local_path:
                    img["src"] = local_path
                    # Remove data-src if present
                    if img.get("data-src"):
                        del img["data-src"]

    # Update link tags (CSS, etc.)
    for link in soup.find_all("link"):
        href = link.get("href")
        if href:
            link["href"] = make_absolute(href, base_url)

    # Update script tags
    for script in soup.find_all("script"):
        src = script.get("src")
        if src:
            script["src"] = make_absolute(src, base_url)

    # Remove unwanted elements (nav, footer, ads, etc.)
    unwanted_selectors = [
        "nav", "footer", "header",
        ".sidebar", ".ad", ".advertisement",
        ".login-modal", ".popup",
        "script:not([src])",  # Inline scripts not needed for PDF
    ]

    for selector in unwanted_selectors:
        for element in soup.select(selector):
            element.decompose()

    # Add print-specific CSS
    style = soup.find("style")
    if style:
        style.append("""
            @media print {
                body { padding: 20px; }
                img { max-width: 100% !important; }
            }
        """)

    return str(soup)


def extract_article_content(html_content):
    """Extract the main article content from HTML.

    Args:
        html_content: HTML content string

    Returns:
        str: Main content HTML
    """
    soup = BeautifulSoup(html_content, "lxml")

    # Try to find article content in common containers
    content_selectors = [
        ".article-content",
        ".article-body",
        ".post-content",
        ".content",
        "article",
        ".main-content",
    ]

    for selector in content_selectors:
        content = soup.select_one(selector)
        if content:
            return str(content)

    # Fallback: return body
    body = soup.find("body")
    if body:
        return str(body)

    return html_content
