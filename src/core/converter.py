"""PDF conversion module using Playwright."""

import json
from pathlib import Path
from typing import Union, Dict

from .exceptions import ConversionError
from ..models.pdf_options import PDFOptions
from ..utils.constants import ConversionConstants, ViewportConstants
from ..utils.selectors import load_selectors, get_platform_from_url
from ..utils.javascript import ScriptManager


def convert_with_context(url, context, output_path, options=None):
    """Convert a URL to PDF using an existing browser context.

    This function reuses an existing browser context to generate PDF,
    avoiding the need to login for each URL.

    Args:
        url: URL to convert
        context: Existing Playwright browser context (with cookies already set)
        output_path: Path for output PDF
        options: Optional PDFOptions instance or dict with keys:
            - page_size: Page size (default: 'A4')
            - landscape: Whether to use landscape orientation

    Returns:
        Path: Path to generated PDF

    Raises:
        ConversionError: If conversion fails
    """
    if options is None:
        options = PDFOptions()
    elif isinstance(options, dict):
        options = PDFOptions.from_dict(options)
    elif not isinstance(options, PDFOptions):
        options = PDFOptions()

    page_size = options.page_size
    landscape = options.landscape

    # Load platform-specific selectors
    platform = get_platform_from_url(url)
    selectors = load_selectors(platform)

    # Build selectors config for JavaScript injection
    fixed_elements = selectors.get("fixed_elements", {})
    if isinstance(fixed_elements, dict):
        fixed_classnames = fixed_elements.get("classnames", [])
        fixed_texts = fixed_elements.get("texts", [])
    else:
        fixed_classnames = fixed_elements if isinstance(fixed_elements, list) else []
        fixed_texts = []

    selectors_config = {
        "sidebar": selectors.get("sidebar", []),
        "article_content": selectors.get("article_content", []),
        "scroll_container": selectors.get("scroll_container", []),
        "fixed_classnames": fixed_classnames,
        "fixed_texts": fixed_texts,
        "exclude_classes": selectors.get("exclude_classes", ["sidebar", "catalog", "menu", "nav", "list"])
    }
    selectors_json = json.dumps(selectors_config, ensure_ascii=False)

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
        page.goto(url, wait_until="load", timeout=ConversionConstants.NAVIGATION_TIMEOUT_MS)
        page.wait_for_timeout(ConversionConstants.PAGE_LOAD_WAIT_MS)

        # Remove floating layers
        print("  移除页面浮层...")
        ScriptManager.execute_script(page, "remove_floating_layers", selectors_json)
        page.wait_for_timeout(ConversionConstants.SHORT_WAIT_MS)

        # Hide left sidebar and expand content area
        print("  隐藏左侧导航栏并扩展内容区域...")
        ScriptManager.execute_script(page, "hide_sidebar", selectors_json)
        page.wait_for_timeout(ConversionConstants.SHORT_WAIT_MS)

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
        container_info = ScriptManager.execute_script(page, "find_content", selectors_json)
        print(f"  容器信息: {container_info}")

        # Scroll to load all content
        print("  滚动加载完整内容...")
        scroll_result = ScriptManager.execute_script(page, "scroll_content", selectors_json)
        print(f"  滚动结果: {scroll_result}")
        page.wait_for_timeout(ConversionConstants.MEDIUM_WAIT_MS)

        # Get final page height
        final_height = page.evaluate("document.documentElement.scrollHeight")
        print(f"  页面总高度: {final_height}px")

        # Scroll back to top
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(ConversionConstants.SHORT_WAIT_MS)

        # Set viewport
        viewport_width = ViewportConstants.VIEWPORT_WIDTH
        viewport_height = max(final_height, ViewportConstants.MIN_VIEWPORT_HEIGHT)
        print(f"  设置视口: {viewport_width} x {viewport_height}")
        page.set_viewport_size({"width": viewport_width, "height": viewport_height})
        page.wait_for_timeout(ConversionConstants.MEDIUM_WAIT_MS)

        # Ensure content area is expanded to full screen
        print("  确保内容区域全屏显示...")
        page.evaluate(f'''((selectors) => {{
            const articleContentSelectors = selectors.article_content || [];
            const scrollContainerSelectors = selectors.scroll_container || [];

            let contentEl = null;
            for (const sel of articleContentSelectors) {{
                contentEl = document.querySelector(sel);
                if (contentEl) break;
            }}

            if (contentEl) {{
                contentEl.style.position = 'absolute';
                contentEl.style.left = '0';
                contentEl.style.top = '0';
                contentEl.style.width = '1920px';
                contentEl.style.height = '100%';
                contentEl.style.maxWidth = 'none';
                contentEl.style.zIndex = '100';

                let scrollContainer = null;
                for (const sel of scrollContainerSelectors) {{
                    scrollContainer = contentEl.querySelector(sel);
                    if (scrollContainer) break;
                }}
                if (scrollContainer) {{
                    scrollContainer.style.position = 'absolute';
                    scrollContainer.style.left = '0';
                    scrollContainer.style.width = '1920px';
                    scrollContainer.style.maxHeight = 'none';
                    scrollContainer.style.height = 'auto';
                    scrollContainer.style.overflow = 'visible';
                }}

                return {{ expanded: true, width: 1920 }};
            }}

            document.body.querySelectorAll(':scope > div').forEach(el => {{
                const rect = el.getBoundingClientRect();
                if (rect.left < 100 && rect.width < 1000) {{
                    el.style.position = 'absolute';
                    el.style.left = '0';
                    el.style.width = '1920px';
                }}
            }});

            return {{ expanded: false }};
        }})(''' + selectors_json + ''')''')
        page.wait_for_timeout(ConversionConstants.SHORT_WAIT_MS)

        # Expand content container to full height
        print("  展开内容容器到完整高度...")
        expand_result = ScriptManager.execute_script(page, "expand_content", selectors_json)
        print(f"  展开结果: {expand_result}")
        page.wait_for_timeout(ConversionConstants.MEDIUM_WAIT_MS)

        # Generate PDF
        content_height = expand_result.get('loadedScrollHeight', ViewportConstants.DEFAULT_CONTENT_HEIGHT)
        pdf_width = ViewportConstants.VIEWPORT_WIDTH
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


