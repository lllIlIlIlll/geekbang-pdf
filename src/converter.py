"""PDF conversion module using Playwright and Puppeteer."""

import os
import tempfile
import subprocess
import json
from pathlib import Path

from .exceptions import ConversionError


def get_page_content_from_chrome(debugging_port=28800):
    """Get page content from existing Chrome session.

    Args:
        debugging_port: Chrome remote debugging port (default: 28800)

    Returns:
        tuple: (html_content, title, url)
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_experimental_option("debuggerAddress", f"localhost:{debugging_port}")

    driver = webdriver.Chrome(options=options)

    try:
        url = driver.current_url
        title = driver.title
        html_content = driver.page_source
        return html_content, title, url
    finally:
        driver.quit()


def convert_chrome_page_to_pdf(debugging_port, output_path, options=None):
    """Convert existing Chrome page to PDF.

    Connects to existing Chrome session and generates PDF from current page.

    Args:
        debugging_port: Chrome remote debugging port
        output_path: Path for output PDF
        options: Optional dict with keys:
            - page_size: Page size (default: 'A4')
            - landscape: Whether to use landscape orientation

    Returns:
        Path: Path to generated PDF

    Raises:
        ConversionError: If conversion fails
    """
    options = options or {}
    page_size = options.get("page_size", "A4")
    landscape = options.get("landscape", False)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create Puppeteer script that connects to existing Chrome
    # Use regular string concatenation to avoid shell interpolation issues with !
    script_parts = [
        "const puppeteer = require('puppeteer');",
        "",
        "(async () => {",
        "    const browser = await puppeteer.connect({",
        f"        browserURL: 'http://localhost:{debugging_port}'",
        "    });",
        "",
        "    const pages = await browser.pages();",
        "    let page = pages.find(p => p.url().includes('geekbang'));",
        "    if (page === undefined) page = pages[0];",
        "",
        "    console.log('Using page:', await page.url());",
        "",
        "    await page.pdf({",
        f"        path: '{output_path.as_posix()}',",
        f"        format: '{page_size}',",
        f"        landscape: {str(landscape).lower()},",
        "        printBackground: true,",
        "        margin: {",
        "            top: '20mm',",
        "            bottom: '20mm',",
        "            left: '15mm',",
        "            right: '15mm'",
        "        }",
        "    });",
        "",
        "    await browser.disconnect();",
        "    console.log('PDF generated successfully');",
        "})();"
    ]
    script_content = "\n".join(script_parts)

    # Write script to temp file using binary mode to avoid any encoding issues
    script_fd, script_path = tempfile.mkstemp(suffix=".js", prefix="puppeteer_script_")
    try:
        os.write(script_fd, script_content.encode('utf-8'))
        os.close(script_fd)
    except Exception:
        os.close(script_fd)
        raise

    try:
        project_root = Path(__file__).parent.parent
        node_modules_path = project_root / "node_modules"

        env = os.environ.copy()
        env["NODE_PATH"] = str(node_modules_path)

        result = subprocess.run(
            ["node", script_path],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
            cwd=str(project_root)
        )

        if result.returncode != 0:
            raise ConversionError(f"Puppeteer conversion failed: {result.stderr}")

        if not output_path.exists():
            raise ConversionError(f"PDF was not generated at {output_path}")

        return output_path

    except subprocess.TimeoutExpired:
        raise ConversionError("PDF conversion timed out")
    except subprocess.SubprocessError as e:
        raise ConversionError(f"PDF conversion failed: {str(e)}")
    finally:
        try:
            os.unlink(script_path)
        except OSError:
            pass


def write_html_to_temp(html_content):
    """Write HTML content to a temporary file.

    Args:
        html_content: HTML string

    Returns:
        Path: Path to temporary HTML file
    """
    fd, path = tempfile.mkstemp(suffix=".html", prefix="geekbang_pdf_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(html_content)
        return Path(path)
    except Exception:
        # Close fd if write failed
        os.close(fd)
        raise


def convert_with_cookie(url, cookie, output_path, options=None):
    """Convert a URL to PDF using Playwright with provided cookie.

    This handles SPA (Single Page Applications) that require JavaScript rendering.

    Args:
        url: URL to convert
        cookie: Cookie string for authentication
        output_path: Path for output PDF
        options: Optional dict with keys:
            - page_size: Page size (default: 'A4')
            - landscape: Whether to use landscape orientation
            - wait_time: Seconds to wait for dynamic content (default: 5)

    Returns:
        Path: Path to generated PDF

    Raises:
        ConversionError: If conversion fails
    """
    options = options or {}
    page_size = options.get("page_size", "A4")
    landscape = options.get("landscape", False)
    wait_time = options.get("wait_time", 5)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Parse cookie string into Playwright format
    cookies = []
    if cookie:
        for part in cookie.split(";"):
            part = part.strip()
            if "=" in part:
                name, value = part.split("=", 1)
                cookies.append({
                    "name": name.strip(),
                    "value": value.strip(),
                    "domain": ".geekbang.org",
                    "path": "/"
                })

    cookies_json = json.dumps(cookies)

    # Create Playwright script
    script_content = f"""
const {{ chromium }} = require('playwright');

(async () => {{
    const browser = await chromium.launch({{
        headless: false,
        args: [
            '--disable-blink-features=AutomationControlled',
            '--disable-infobars',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu'
        ]
    }});

    // Stealth mode - hide automation
    const context = await browser.newContext({{
        viewport: {{ width: 1920, height: 1080 }},
        user_agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }});

    const page = await context.newPage();

    // Hide webdriver property
    await page.addInitScript(() => {{
        Object.defineProperty(navigator, 'webdriver', {{ get: () => false }});
    }});

    // Set cookies if provided
    const cookies = {cookies_json};
    if (cookies.length > 0) {{
        await context.addCookies(cookies);
    }}

    // Navigate to URL
    console.log('Navigating to:', '{url}');
    await page.goto('{url}', {{
        waitUntil: 'load',
        timeout: 30000
    }});

    // Wait for initial content to load
    await page.waitForTimeout({wait_time * 1000});

    // Scroll to bottom multiple times to load all dynamic content
    console.log('Scrolling to load all content...');
    await page.evaluate(async () => {{
        // Scroll down multiple times, waiting for new content to load
        let lastHeight = 0;
        let sameHeightCount = 0;
        const maxScrolls = 50;  // Max number of scroll attempts

        for (let i = 0; i < maxScrolls; i++) {{
            // Scroll to bottom
            window.scrollTo(0, document.body.scrollHeight);

            // Wait for content to load
            await new Promise(resolve => setTimeout(resolve, 500));

            // Check if we've reached the bottom
            let newHeight = document.body.scrollHeight;
            if (newHeight === lastHeight) {{
                sameHeightCount++;
                if (sameHeightCount >= 3) {{
                    // Stop scrolling if height hasn't changed 3 times in a row
                    break;
                }}
            }} else {{
                sameHeightCount = 0;
            }}
            lastHeight = newHeight;
        }}

        // Scroll back to top
        window.scrollTo(0, 0);
        await new Promise(resolve => setTimeout(resolve, 500));
    }});

    // Wait after scrolling
    await page.waitForTimeout(3000);

    // Generate PDF
    console.log('Generating PDF...');
    await page.pdf({{
        path: '{output_path.as_posix()}',
        format: '{page_size}',
        landscape: {str(landscape).lower()},
        printBackground: true,
        fullPage: true,
        margin: {{
            top: '20mm',
            bottom: '20mm',
            left: '15mm',
            right: '15mm'
        }}
    }});

    await browser.close();
    console.log('PDF generated successfully');
}})();
"""

    # Write script to temp file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".js",
        prefix="playwright_script_",
        delete=False,
        encoding="utf-8"
    ) as f:
        f.write(script_content)
        script_path = f.name

    try:
        # Get project root for node_modules
        project_root = Path(__file__).parent.parent
        node_modules_path = project_root / "node_modules"

        # Set NODE_PATH so playwright can be found
        env = os.environ.copy()
        env["NODE_PATH"] = str(node_modules_path)

        # Run the script with Node.js
        result = subprocess.run(
            ["node", script_path],
            capture_output=True,
            text=True,
            timeout=180,
            env=env,
            cwd=str(project_root)
        )

        if result.returncode != 0:
            raise ConversionError(
                f"Playwright conversion failed: {result.stderr}"
            )

        if not output_path.exists():
            raise ConversionError(
                f"PDF was not generated at {output_path}"
            )

        return output_path

    except subprocess.TimeoutExpired:
        raise ConversionError("PDF conversion timed out")
    except subprocess.SubprocessError as e:
        raise ConversionError(f"PDF conversion failed: {str(e)}")
    finally:
        # Clean up script
        try:
            os.unlink(script_path)
        except OSError:
            pass


def cleanup_temp_files(*paths):
    """Clean up temporary files.

    Args:
        *paths: File paths to remove
    """
    for path in paths:
        try:
            path = Path(path)
            if path.exists():
                path.unlink()
        except OSError:
            pass
