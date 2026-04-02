"""Selenium-based login automation for GeekBang."""

import os
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from .exceptions import AuthError


# Chrome user data directory on macOS
CHROME_USER_DATA_DIR = Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
# QClaw browser also uses Chrome, check there too
QCLAW_CHROME_USER_DATA_DIR = Path.home() / ".qclaw" / "browser" / "openclaw" / "user-data"


def get_chrome_user_data_dir():
    """Get the active Chrome user data directory.

    Returns:
        Path: Path to the user data directory with active Chrome profile
    """
    # Check standard Chrome first
    if CHROME_USER_DATA_DIR.exists():
        default_cookies = CHROME_USER_DATA_DIR / "Default" / "Cookies"
        if default_cookies.exists():
            try:
                import sqlite3
                import tempfile
                import shutil
                temp_dir = tempfile.mkdtemp()
                temp_db = os.path.join(temp_dir, "cookies.db")
                shutil.copyfile(default_cookies, temp_db)
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM cookies WHERE host_key LIKE '%geekbang%'")
                count = cursor.fetchone()[0]
                conn.close()
                shutil.rmtree(temp_dir)
                if count > 0:
                    return CHROME_USER_DATA_DIR
            except Exception:
                pass

    # Check QClaw Chrome
    if QCLAW_CHROME_USER_DATA_DIR.exists():
        return QCLAW_CHROME_USER_DATA_DIR

    return CHROME_USER_DATA_DIR


def get_chrome_options(headless=True, profile_dir=None):
    """Get Chrome options for headless browsing.

    Args:
        headless: Whether to run in headless mode
        profile_dir: Optional Chrome profile directory name (e.g., 'Default', 'Profile 1')

    Returns:
        Options: Chrome options object
    """
    options = Options()
    if headless:
        options.add_argument("--headless=new")  # Use new headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # Use existing Chrome profile if specified
    if profile_dir and CHROME_USER_DATA_DIR.exists():
        profile_path = CHROME_USER_DATA_DIR / profile_dir
        if profile_path.exists():
            options.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
            options.add_argument(f"--profile-directory={profile_dir}")

    return options


def login(email, password, headless=True):
    """Login to geekbang.org using Selenium.

    Args:
        email: Email address for login
        password: Password for login
        headless: Whether to run browser in headless mode

    Returns:
        str: Session cookie string

    Raises:
        AuthError: If login fails
    """
    driver = None
    try:
        options = get_chrome_options(headless=headless)
        driver = webdriver.Chrome(options=options)

        # Navigate to login page
        driver.get("https://account.geekbang.org/login")

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "login"))
        )

        # Find and fill email input
        email_input = driver.find_element(By.CSS_SELECTOR, "input[type='email'], input[name='email']")
        email_input.clear()
        email_input.send_keys(email)

        # Find and fill password input
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
        password_input.clear()
        password_input.send_keys(password)

        # Click login button
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .login-btn")
        login_button.click()

        # Wait for login to complete (check for redirect or specific element)
        time.sleep(3)

        # Extract cookies
        cookies = driver.get_cookies()
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

        if not cookie_str:
            raise AuthError("Failed to obtain session cookie")

        return cookie_str

    except Exception as e:
        raise AuthError(f"Login failed: {str(e)}")
    finally:
        if driver:
            driver.quit()


def login_with_cookie(cookie, headless=True):
    """Verify a cookie by using it to access a protected page.

    Args:
        cookie: Cookie string to verify
        headless: Whether to run browser in headless mode

    Returns:
        bool: True if cookie is valid

    Raises:
        AuthError: If verification fails
    """
    driver = None
    try:
        options = get_chrome_options(headless=headless)
        driver = webdriver.Chrome(options=options)

        # Navigate to a protected page
        driver.get("https://time.geekbang.org/")

        # Add cookies
        for c in cookie.split("; "):
            if "=" in c:
                name, value = c.split("=", 1)
                driver.add_cookie({"name": name, "value": value})

        # Refresh to apply cookies
        driver.refresh()
        time.sleep(2)

        # Check if we're logged in by looking for user-specific elements
        current_url = driver.current_url
        return "login" not in current_url.lower()

    except Exception as e:
        raise AuthError(f"Cookie verification failed: {str(e)}")
    finally:
        if driver:
            driver.quit()


def get_cookies_from_existing_chrome(debugging_port=28800, timeout=30):
    """Get cookies from an existing Chrome browser session via Selenium.

    Uses Selenium with Chrome DevTools Protocol to attach to the running
    Chrome instance and get cookies.

    Args:
        debugging_port: Chrome remote debugging port (default: 28800)
        timeout: Seconds to wait for connection

    Returns:
        str: Cookie string for geekbang.org

    Raises:
        AuthError: If cookie extraction fails
    """
    driver = None
    try:
        # Connect to existing Chrome via debugger address
        options = Options()
        options.add_experimental_option("debuggerAddress", f"localhost:{debugging_port}")

        driver = webdriver.Chrome(options=options)

        # Get all cookies
        all_cookies = driver.get_cookies()

        # Filter for geekbang domains
        cookie_parts = []
        for c in all_cookies:
            domain = c.get("domain", "")
            name = c.get("name", "")
            value = c.get("value", "")
            if "geekbang" in domain.lower():
                cookie_parts.append(f"{name}={value}")

        if not cookie_parts:
            # Return all cookies
            cookie_parts = [f"{c.get('name', '')}={c.get('value', '')}" for c in all_cookies]

        cookie_str = "; ".join(cookie_parts)
        if cookie_str:
            return cookie_str

        raise AuthError("No cookies found")

    except Exception as e:
        raise AuthError(f"Failed to get cookies from Chrome: {str(e)}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
