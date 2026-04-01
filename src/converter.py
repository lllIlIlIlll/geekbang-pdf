"""PDF conversion module using Playwright and Puppeteer."""

import os
import tempfile
import subprocess
import json
from pathlib import Path

from .exceptions import ConversionError


def convert_with_context(url, context, output_path, options=None):
    """Convert a URL to PDF using an existing browser context.

    This function reuses an existing browser context to generate PDF,
    avoiding the need to login for each URL.

    Args:
        url: URL to convert
        context: Existing Playwright browser context (with cookies already set)
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

    # Create a new page in the existing context
    page = context.new_page()

    try:
        # Set User-Agent
        page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # Navigate to URL
        print(f"  正在打开: {url}")
        page.goto(url, wait_until="load", timeout=60000)
        page.wait_for_timeout(8000)

        # Remove floating layers
        print("  移除页面浮层...")
        page.evaluate('''() => {
            const toRemove = [];
            document.querySelectorAll('*').forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.position === 'fixed' || style.position === 'sticky') {
                    const text = el.innerText || '';
                    const classes = el.className || '';
                    if ((text.includes('登录') && text.includes('注册')) ||
                        text.includes('推荐试读') ||
                        text.includes('仅针对订阅') ||
                        classes.includes('modal') ||
                        classes.includes('popup') ||
                        classes.includes('overlay')) {
                        toRemove.push(el);
                    }
                }
            });
            toRemove.forEach(el => el.remove());
        }''')
        page.wait_for_timeout(1000)

        # Hide left sidebar and expand content area
        print("  隐藏左侧导航栏并扩展内容区域...")
        page.evaluate('''() => {
            let hiddenCount = 0;

            // 1. Hide left sidebar
            document.querySelectorAll('[class*="Index_side"]').forEach(el => {
                el.style.display = 'none';
                hiddenCount++;
            });

            // 2. Hide right fixed elements
            document.querySelectorAll('*').forEach(el => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                const classes = el.className || '';
                if (style.position === 'fixed' && rect.left > 1000 && rect.width < 400) {
                    el.style.display = 'none';
                    hiddenCount++;
                }
            });

            // 3. Find and expand main content area
            const contentSelectors = [
                '[class*="Index_contentWrap"]',
                '[class*="contentWrap"]',
                '[class*="article-container"]',
                'article',
                'main'
            ];

            let contentEl = null;
            for (const sel of contentSelectors) {
                const el = document.querySelector(sel);
                if (el) {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 500 && rect.height > 300) {
                        contentEl = el;
                        break;
                    }
                }
            }

            if (contentEl) {
                contentEl.style.position = 'absolute';
                contentEl.style.left = '0';
                contentEl.style.top = '0';
                contentEl.style.width = '100%';
                contentEl.style.maxWidth = 'none';
                contentEl.style.height = '100%';
                contentEl.style.zIndex = '100';

                const scrollContainer = contentEl.querySelector('[class*="contentWrapper"], [class*="scroller"], .simplebar-content-wrapper');
                if (scrollContainer) {
                    scrollContainer.style.position = 'absolute';
                    scrollContainer.style.left = '0';
                    scrollContainer.style.width = '100%';
                }
            }

            return { hiddenCount, contentEl: contentEl ? contentEl.className : null };
        }''')
        page.wait_for_timeout(1000)

        # Get page title for filename
        page_title = page.title()
        safe_title = "".join(c for c in page_title if c.isalnum() or c in (' ', '-', '_', '｜')).strip()
        safe_title = safe_title.replace(' ', '_')

        # If output_path is the default name, use the page title
        if output_path.name == "geekbang_article.pdf":
            output_path = output_path.parent / f"{safe_title}.pdf"

        print(f"  页面标题: {page_title}")
        print(f"  输出文件: {output_path.name}")

        # Find and scroll content container
        print("  查找文章内容容器...")
        container_info = page.evaluate('''() => {
            const selectors = [
                '[class*="article"]',
                '[class*="content"]',
                '[class*="article-content"]',
                '[class*="post-content"]',
                '[id*="article"]',
                '[id*="content"]',
                'main',
                'article',
                '.main-content'
            ];

            let contentContainer = null;
            let maxHeight = 0;

            document.querySelectorAll('div').forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.overflowY === 'auto' || style.overflowY === 'scroll' ||
                    style.overflow === 'auto' || style.overflow === 'scroll') {
                    const rect = el.getBoundingClientRect();
                    const scrollHeight = el.scrollHeight;
                    if (scrollHeight > maxHeight && rect.height > 500 &&
                        !el.className.includes('sidebar') &&
                        !el.className.includes('catalog') &&
                        !el.className.includes('menu') &&
                        !el.className.includes('nav')) {
                        maxHeight = scrollHeight;
                        contentContainer = el;
                    }
                }
            });

            if (!contentContainer) {
                for (const selector of selectors) {
                    const el = document.querySelector(selector);
                    if (el) {
                        const rect = el.getBoundingClientRect();
                        const scrollHeight = el.scrollHeight;
                        if (scrollHeight > 500 && rect.height > 500) {
                            contentContainer = el;
                            break;
                        }
                    }
                }
            }

            if (!contentContainer) {
                let maxScrollHeight = 0;
                document.body.querySelectorAll(':scope > div').forEach(el => {
                    const scrollHeight = el.scrollHeight;
                    const rect = el.getBoundingClientRect();
                    if (scrollHeight > maxScrollHeight && rect.height > 500) {
                        maxScrollHeight = scrollHeight;
                        contentContainer = el;
                    }
                });
            }

            if (contentContainer) {
                return {
                    found: true,
                    tagName: contentContainer.tagName,
                    className: contentContainer.className,
                    id: contentContainer.id,
                    scrollHeight: contentContainer.scrollHeight,
                    clientHeight: contentContainer.clientHeight,
                    rectHeight: contentContainer.getBoundingClientRect().height
                };
            }

            return { found: false };
        }''')
        print(f"  容器信息: {container_info}")

        # Scroll to load all content
        print("  滚动加载完整内容...")
        scroll_result = page.evaluate('''() => {
            let scrollContainer = null;
            let maxHeight = 0;

            document.querySelectorAll('div').forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.overflowY === 'auto' || style.overflowY === 'scroll' ||
                    style.overflow === 'auto' || style.overflow === 'scroll') {
                    const scrollHeight = el.scrollHeight;
                    const rect = el.getBoundingClientRect();
                    if (scrollHeight > maxHeight && rect.height > 500 &&
                        !el.className.includes('sidebar') &&
                        !el.className.includes('catalog') &&
                        !el.className.includes('menu') &&
                        !el.className.includes('nav') &&
                        !el.className.includes('list')) {
                        maxHeight = scrollHeight;
                        scrollContainer = el;
                    }
                }
            });

            if (!scrollContainer) {
                window.scrollTo(0, document.body.scrollHeight);
                return { method: 'window', scrollHeight: document.body.scrollHeight };
            }

            const finalHeight = scrollContainer.scrollHeight;
            let scrolled = 0;
            const scrollStep = window.innerHeight;

            while (scrolled < finalHeight) {
                scrollContainer.scrollTop += scrollStep;
                scrolled += scrollStep;
                if (typeof requestAnimationFrame === 'function') {
                    requestAnimationFrame(() => {});
                }
            }

            scrollContainer.scrollTop = 0;

            return {
                method: 'container',
                containerClass: scrollContainer.className,
                scrollHeight: finalHeight
            };
        }''')
        print(f"  滚动结果: {scroll_result}")
        page.wait_for_timeout(2000)

        # Get final page height
        final_height = page.evaluate("document.documentElement.scrollHeight")
        print(f"  页面总高度: {final_height}px")

        # Scroll back to top
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)

        # Set viewport
        viewport_width = 1920
        viewport_height = max(final_height, 4000)
        print(f"  设置视口: {viewport_width} x {viewport_height}")
        page.set_viewport_size({"width": viewport_width, "height": viewport_height})
        page.wait_for_timeout(2000)

        # Ensure content area is expanded to full screen
        print("  确保内容区域全屏显示...")
        page.evaluate('''() => {
            const contentEl = document.querySelector('[class*="Index_contentWrap"]');
            if (contentEl) {
                contentEl.style.position = 'absolute';
                contentEl.style.left = '0';
                contentEl.style.top = '0';
                contentEl.style.width = '1920px';
                contentEl.style.height = '100%';
                contentEl.style.maxWidth = 'none';
                contentEl.style.zIndex = '100';

                const scrollContainer = contentEl.querySelector('[class*="scroller"], .simplebar-content-wrapper');
                if (scrollContainer) {
                    scrollContainer.style.position = 'absolute';
                    scrollContainer.style.left = '0';
                    scrollContainer.style.width = '1920px';
                    scrollContainer.style.maxHeight = 'none';
                    scrollContainer.style.height = 'auto';
                    scrollContainer.style.overflow = 'visible';
                }

                return { expanded: true, width: 1920 };
            }

            document.body.querySelectorAll(':scope > div').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.left < 100 && rect.width < 1000) {
                    el.style.position = 'absolute';
                    el.style.left = '0';
                    el.style.width = '1920px';
                }
            });

            return { expanded: false };
        }''')
        page.wait_for_timeout(1000)

        # Expand content container to full height
        print("  展开内容容器到完整高度...")
        expand_result = page.evaluate('''() => {
            let scrollContainer = null;
            let maxHeight = 0;

            document.querySelectorAll('div').forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.overflowY === 'auto' || style.overflowY === 'scroll' ||
                    style.overflow === 'auto' || style.overflow === 'scroll') {
                    const scrollHeight = el.scrollHeight;
                    const rect = el.getBoundingClientRect();
                    if (scrollHeight > maxHeight && rect.height > 500 &&
                        !el.className.includes('sidebar') &&
                        !el.className.includes('catalog') &&
                        !el.className.includes('menu') &&
                        !el.className.includes('nav') &&
                        !el.className.includes('list')) {
                        maxHeight = scrollHeight;
                        scrollContainer = el;
                    }
                }
            });

            if (!scrollContainer) {
                return { expanded: false, error: 'No container found' };
            }

            const originalScrollHeight = scrollContainer.scrollHeight;
            scrollContainer.scrollTop = originalScrollHeight;
            const loadedScrollHeight = scrollContainer.scrollHeight;
            scrollContainer.scrollTop = 0;

            scrollContainer.style.maxHeight = 'none';
            scrollContainer.style.height = (loadedScrollHeight + 500) + 'px';
            scrollContainer.style.overflow = 'visible';

            const parent = scrollContainer.parentElement;
            if (parent && (parent.className.includes('simplebar') || parent.className.includes('SimpleBar'))) {
                parent.style.maxHeight = 'none';
                parent.style.height = (loadedScrollHeight + 500) + 'px';
                parent.style.overflow = 'visible';
                const simplebarEl = parent.querySelector('.simplebar-scrollbar');
                if (simplebarEl) {
                    simplebarEl.style.display = 'none';
                }
            }

            return {
                expanded: true,
                originalScrollHeight: originalScrollHeight,
                loadedScrollHeight: loadedScrollHeight,
                className: scrollContainer.className
            };
        }''')
        print(f"  展开结果: {expand_result}")
        page.wait_for_timeout(2000)

        # Generate PDF
        content_height = expand_result.get('loadedScrollHeight', 25000)
        pdf_width = 1920
        print(f"  正在生成 PDF (宽度: {pdf_width}px, 内容高度: {content_height}px)...")

        page.pdf(
            path=str(output_path),
            width=f"{pdf_width}px",
            height=f"{content_height}px",
            print_background=True,
            margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"}
        )

        return output_path

    finally:
        # Always close the page when done
        page.close()


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
