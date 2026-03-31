"""Puppeteer-based PDF conversion module."""

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


def convert_to_pdf(html_path, output_path, options=None):
    """Convert HTML file to PDF using Puppeteer.

    Args:
        html_path: Path to HTML file
        output_path: Path for output PDF
        options: Optional dict with keys:
            - page_size: Page size (default: 'A4')
            - landscape: Whether to use landscape orientation
            - print_background: Whether to print background graphics

    Returns:
        Path: Path to generated PDF

    Raises:
        ConversionError: If conversion fails
    """
    options = options or {}
    page_size = options.get("page_size", "A4")
    landscape = options.get("landscape", False)
    print_background = options.get("print_background", True)

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create Puppeteer script
    script_content = f"""
const puppeteer = require('puppeteer');
const path = require('path');

(async () => {{
    const browser = await puppeteer.launch({{
        headless: true,
        executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }});

    const page = await browser.newPage();

    // Set viewport
    await page.setViewport({{
        width: 1200,
        height: 800,
        deviceScaleFactor: 1
    }});

    // Load HTML file
    const htmlPath = '{html_path.as_posix()}';
    await page.goto(`file:///${{htmlPath}}`, {{
        waitUntil: 'networkidle0'
    }});

    // Wait a bit for any dynamic content
    await page.waitForTimeout(1000);

    // Generate PDF
    await page.pdf({{
        path: '{output_path.as_posix()}',
        format: '{page_size}',
        landscape: {str(landscape).lower()},
        printBackground: {str(print_background).lower()},
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
        prefix="puppeteer_script_",
        delete=False
    ) as f:
        f.write(script_content)
        script_path = f.name

    try:
        # Get project root for node_modules
        project_root = Path(__file__).parent.parent
        node_modules_path = project_root / "node_modules"

        # Set NODE_PATH so puppeteer can be found
        env = os.environ.copy()
        env["NODE_PATH"] = str(node_modules_path)

        # Run the script with Node.js
        result = subprocess.run(
            ["node", script_path],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
            cwd=str(project_root)  # Run from project root
        )

        if result.returncode != 0:
            raise ConversionError(
                f"Puppeteer conversion failed: {result.stderr}"
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


def convert_url_to_pdf(url, output_path, cookies=None, options=None):
    """Convert a URL directly to PDF using Puppeteer.

    This handles SPA (Single Page Applications) that require JavaScript rendering.

    Args:
        url: URL to convert
        output_path: Path for output PDF
        cookies: Optional cookie string or dict for authentication
        options: Optional dict with keys:
            - page_size: Page size (default: 'A4')
            - landscape: Whether to use landscape orientation
            - print_background: Whether to print background graphics
            - wait_time: Seconds to wait for dynamic content (default: 3)

    Returns:
        Path: Path to generated PDF

    Raises:
        ConversionError: If conversion fails
    """
    options = options or {}
    page_size = options.get("page_size", "A4")
    landscape = options.get("landscape", False)
    print_background = options.get("print_background", True)
    wait_time = options.get("wait_time", 3)

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Parse cookies into JavaScript array format
    cookies_js = "[]"
    if cookies:
        if isinstance(cookies, str):
            from .fetcher import parse_cookie_string
            cookie_dict = parse_cookie_string(cookies)
        else:
            cookie_dict = cookies

        cookies_js = json.dumps([
            {"name": k, "value": v, "domain": ".geekbang.org", "path": "/"}
            for k, v in cookie_dict.items()
        ])

    # Create Puppeteer script for URL
    script_content = f"""
const puppeteer = require('puppeteer');

(async () => {{
    const browser = await puppeteer.launch({{
        headless: true,
        executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }});

    const page = await browser.newPage();

    // Set viewport
    await page.setViewport({{
        width: 1200,
        height: 800,
        deviceScaleFactor: 1
    }});

    // Set cookies if provided
    const cookies = {cookies_js};
    if (cookies.length > 0) {{
        await page.setCookie(...cookies);
    }}

    // Navigate to URL
    await page.goto('{url}', {{
        waitUntil: 'networkidle2',
        timeout: 60000
    }});

    // Wait for dynamic content to load
    await page.waitForTimeout({wait_time * 1000});

    // Scroll to bottom to load all content
    await page.evaluate(() => {{
        return new Promise((resolve) => {{
            let totalHeight = 0;
            const distance = 100;
            const timer = setInterval(() => {{
                const scrollHeight = document.body.scrollHeight;
                window.scrollBy(0, distance);
                totalHeight += distance;
                if(totalHeight >= scrollHeight){{
                    clearInterval(timer);
                    resolve();
                }}
            }}, 100);
        }});
    }});

    // Wait after scrolling
    await page.waitForTimeout(2000);

    // Generate PDF
    await page.pdf({{
        path: '{output_path.as_posix()}',
        format: '{page_size}',
        landscape: {str(landscape).lower()},
        printBackground: {str(print_background).lower()},
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
        prefix="puppeteer_script_",
        delete=False
    ) as f:
        f.write(script_content)
        script_path = f.name

    try:
        # Get project root for node_modules
        project_root = Path(__file__).parent.parent
        node_modules_path = project_root / "node_modules"

        # Set NODE_PATH so puppeteer can be found
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
                f"Puppeteer conversion failed: {result.stderr}"
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
