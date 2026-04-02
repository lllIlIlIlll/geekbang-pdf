"""Smart waiting utilities for Playwright operations."""

from typing import Optional

try:
    from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
except ImportError:
    Page = None
    PlaywrightTimeoutError = Exception


class SmartWaits:
    """Smart waiting utilities for page operations."""

    @staticmethod
    def wait_for_network_idle(page: Page, timeout: int = 15000) -> bool:
        """Wait for the page to reach network idle state.

        Args:
            page: Playwright page object
            timeout: Timeout in milliseconds (default: 15000)

        Returns:
            bool: True if network idle was reached, False if timeout
        """
        if Page is None:
            return False

        try:
            page.wait_for_load_state("networkidle", timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    @staticmethod
    def wait_for_content_loaded(
        page: Page,
        selector: str = "article",
        timeout: int = 30000
    ) -> bool:
        """Wait for specific content to be loaded and visible.

        Args:
            page: Playwright page object
            selector: CSS selector to wait for (default: 'article')
            timeout: Timeout in milliseconds (default: 30000)

        Returns:
            bool: True if selector was found, False if timeout
        """
        if Page is None:
            return False

        try:
            page.wait_for_selector(selector, state="visible", timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    @staticmethod
    def wait_for_element_attribute(
        page: Page,
        selector: str,
        attribute: str,
        value: str,
        timeout: int = 10000
    ) -> bool:
        """Wait for an element's attribute to have a specific value.

        Args:
            page: Playwright page object
            selector: CSS selector for the element
            attribute: Attribute name to check
            value: Expected attribute value
            timeout: Timeout in milliseconds (default: 10000)

        Returns:
            bool: True if attribute matches, False if timeout
        """
        if Page is None:
            return False

        from playwright.sync_api import ExpectedConditions

        try:
            element = page.wait_for_selector(selector, timeout=timeout)
            return element.get_attribute(attribute) == value
        except PlaywrightTimeoutError:
            return False

    @staticmethod
    def scroll_to_bottom(page: Page) -> int:
        """Scroll to the bottom of the page, loading all dynamic content.

        Args:
            page: Playwright page object

        Returns:
            int: Final scroll height after scrolling
        """
        if Page is None:
            return 0

        last_height = 0
        same_height_count = 0
        max_scrolls = 50

        for _ in range(max_scrolls):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(500)

            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                same_height_count += 1
                if same_height_count >= 3:
                    break
            else:
                same_height_count = 0

            last_height = new_height

        # Scroll back to top
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(300)

        return last_height
