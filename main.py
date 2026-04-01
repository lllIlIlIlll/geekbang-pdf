#!/usr/bin/env python3
"""CLI entry point for GeekBang PDF Saver."""

import sys
import argparse
import os
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src import (
    URLInvalidError,
    FetchError,
    AuthError,
    ConversionError,
    ConfigError,
)
from src.auth import login, get_cookies_from_existing_chrome, login_via_browser
from src.fetcher import fetch_page, get_page_title
from src.parser import process_html, extract_article_content
from src.converter import convert_with_cookie, convert_chrome_page_to_pdf, write_html_to_temp, cleanup_temp_files
from playwright.sync_api import sync_playwright
from config.config import (
    load_config,
    save_config,
    get_cookie,
    set_cookie,
    get_default_output_dir,
    set_default_output_dir,
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="保存极客时间课程页面为 PDF 文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 使用浏览器登录（推荐）
  python main.py <url> --browser-login

  # 使用已保存的 Cookie
  python main.py <url> --use-config
        """
    )

    parser.add_argument("url", nargs="?", help="极客时间文章 URL")
    parser.add_argument("-o", "--output", metavar="DIR", help="PDF 输出目录")
    parser.add_argument("-n", "--name", metavar="NAME", help="输出文件名")
    parser.add_argument("--cookie", metavar="COOKIE", help="会话 Cookie")
    parser.add_argument("--use-config", action="store_true", help="使用配置文件中的 Cookie")
    parser.add_argument("--use-chrome", action="store_true", help="从 Chrome 浏览器获取 Cookie")
    parser.add_argument("--login", action="store_true", help="手动登录并保存 Cookie")
    parser.add_argument("--browser-login", action="store_true", help="通过浏览器登录")
    parser.add_argument("--page-size", choices=["A4", "Letter", "Legal"], default="A4")
    parser.add_argument("--landscape", action="store_true")
    parser.add_argument("--set-default-dir", metavar="DIR")

    return parser.parse_args()


def handle_login(args):
    """Handle login operation."""
    try:
        print("正在登录极客时间...")
        cookie = login(email=args.email, password=args.password, headless=False, interactive=True)
        set_cookie(cookie)
        print("登录成功！Cookie 已保存。")
        return 0
    except AuthError as e:
        print(f"登录失败: {e}")
        return 1


def browser_login_and_save(args):
    """Browser login then navigate to URL and save as PDF.

    This function:
    1. Opens login page in a new tab
    2. Waits for user to login manually
    3. Opens article URL in another tab
    4. Waits for content to load
    5. Removes floating layers
    6. Scrolls to load all content
    7. Generates PDF with full_page=True
    """
    if not args.url:
        print("错误: URL 是必需的")
        return 1

    # Determine output directory
    output_dir = args.output or get_default_output_dir()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine output filename
    if args.name:
        output_name = args.name
    else:
        output_name = "geekbang_article"

    output_path = output_dir / f"{output_name}.pdf"

    print("\n" + "="*50)
    print("极客时间 PDF 生成器")
    print("="*50)
    print()
    print("请在浏览器中完成以下步骤:")
    print("1. 登录极客时间")
    print("2. 登录成功后，在终端按 Enter 键继续")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 步骤1: 打开登录页面
        print("正在打开登录页面...")
        page.goto("https://account.geekbang.org/login", wait_until="load", timeout=60000)

        # 等待用户登录 - 自动检测登录状态
        print("等待登录完成...")

        # 检查登录状态的 JavaScript
        check_login_js = '''() => {
            // 检查是否已登录：查找用户头像或用户信息元素
            const userElements = document.querySelectorAll('[class*="user"], [class*="avatar"], [class*="profile"]');
            const loginButton = document.querySelector('[class*="login"], [class*="signin"]');

            // 检查 URL 是否已经离开登录页
            const isOnLoginPage = window.location.href.includes('account.geekbang.org/login');

            // 检查是否有用户信息 cookie 相关的元素
            const hasUserInfo = document.querySelector('.user-info, .user-name, .avatar, [class*="loginSuccess"]');

            return {
                isOnLoginPage: isOnLoginPage,
                hasUserElements: userElements.length > 0,
                hasLoginButton: loginButton !== null,
                hasUserInfo: hasUserInfo !== null,
                url: window.location.href
            };
        }'''

        # 等待登录完成 - 轮询检查登录状态
        max_wait_time = 120  # 最多等待 120 秒
        poll_interval = 2  # 每 2 秒检查一次
        elapsed = 0
        login_detected = False

        while elapsed < max_wait_time:
            page.wait_for_timeout(poll_interval * 1000)
            elapsed += poll_interval

            try:
                login_status = page.evaluate(check_login_js)
                print(f"  登录状态检查: {elapsed}/{max_wait_time}s - URL: {login_status['url'][:60]}...")

                # 如果 URL 已经离开登录页，说明登录成功
                if not login_status['isOnLoginPage']:
                    print("  检测到已离开登录页，登录成功!")
                    login_detected = True
                    break

                # 如果页面包含用户信息元素，说明已登录
                if login_status['hasUserInfo'] or (login_status['hasUserElements'] and not login_status['hasLoginButton']):
                    print("  检测到用户信息，已登录")
                    login_detected = True
                    break

            except Exception as e:
                # 页面可能正在导航，忽略错误继续等待
                print(f"  检查登录状态时发生错误 (可能是导航中): {str(e)[:50]}...")
                pass

        # 如果超时且未检测到登录，等待用户操作
        if not login_detected:
            print("  等待超时，请在浏览器中完成登录...")
            page.wait_for_timeout(30000)  # 再等待 30 秒

        # 步骤2: 在新标签页打开目标文章
        print(f"正在打开文章: {args.url}")

        # 创建新页面（标签）
        article_page = context.new_page()
        article_page.goto(args.url, wait_until="load", timeout=60000)
        article_page.wait_for_timeout(8000)

        # 保存 Cookie
        cookies = context.cookies()
        gb_cookies = [c for c in cookies if 'geekbang' in c.get('domain', '').lower()]
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in gb_cookies])
        if cookie_str:
            set_cookie(cookie_str)
            print(f"Cookie 已保存 (长度: {len(cookie_str)})")

        # 步骤3: 移除浮层
        print("移除页面浮层...")
        article_page.evaluate('''() => {
            // 移除固定定位的浮层
            const toRemove = [];
            document.querySelectorAll('*').forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.position === 'fixed' || style.position === 'sticky') {
                    const text = el.innerText || '';
                    const classes = el.className || '';
                    // 浮层特征
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
        article_page.wait_for_timeout(1000)

        # 步骤3.5: 隐藏左侧导航栏并扩展内容区域
        print("隐藏左侧导航栏并扩展内容区域...")
        hide_nav_js = '''() => {
            let hiddenCount = 0;

            // 1. 隐藏左侧导航栏
            document.querySelectorAll('[class*="Index_side"]').forEach(el => {
                el.style.display = 'none';
                hiddenCount++;
            });

            // 2. 隐藏右侧固定元素（如有）
            document.querySelectorAll('*').forEach(el => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                const classes = el.className || '';
                // 隐藏右侧固定定位的元素
                if (style.position === 'fixed' && rect.left > 1000 && rect.width < 400) {
                    el.style.display = 'none';
                    hiddenCount++;
                }
            });

            // 3. 找到并扩展主内容区域
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
                    // 找大的内容容器
                    if (rect.width > 500 && rect.height > 300) {
                        contentEl = el;
                        break;
                    }
                }
            }

            if (contentEl) {
                // 扩展内容区域到全屏
                contentEl.style.position = 'absolute';
                contentEl.style.left = '0';
                contentEl.style.top = '0';
                contentEl.style.width = '100%';
                contentEl.style.maxWidth = 'none';
                contentEl.style.height = '100%';
                contentEl.style.zIndex = '100';

                // 找到内部滚动容器并扩展
                const scrollContainer = contentEl.querySelector('[class*="contentWrapper"], [class*="scroller"], .simplebar-content-wrapper');
                if (scrollContainer) {
                    scrollContainer.style.position = 'absolute';
                    scrollContainer.style.left = '0';
                    scrollContainer.style.width = '100%';
                }
            }

            return { hiddenCount, contentEl: contentEl ? contentEl.className : null };
        }'''

        hide_result = article_page.evaluate(hide_nav_js)
        print(f"  隐藏导航结果: {hide_result}")
        article_page.wait_for_timeout(1000)

        # 获取页面标题用于文件名
        print("获取页面标题...")
        page_title = article_page.title()
        print(f"  页面标题: {page_title}")
        # 清理标题中的非法字符
        safe_title = "".join(c for c in page_title if c.isalnum() or c in (' ', '-', '_', '｜')).strip()
        safe_title = safe_title.replace(' ', '_')
        if args.name:
            output_name = args.name
        else:
            output_name = safe_title
        output_path = output_dir / f"{output_name}.pdf"
        print(f"  输出文件名: {output_name}.pdf")

        # 步骤4: 查找并滚动文章内容容器
        print("查找文章内容容器...")

        # 查找文章内容容器的 JavaScript
        find_scroll_container_js = '''() => {
            // 首先尝试查找常见的文章内容容器
            const selectors = [
                // 极客时间常见的内容容器
                '[class*="article"]',
                '[class*="content"]',
                '[class*="article-content"]',
                '[class*="post-content"]',
                '[id*="article"]',
                '[id*="content"]',
                // 通用容器
                'main',
                'article',
                '.main-content'
            ];

            let contentContainer = null;
            let maxHeight = 0;

            // 方法1: 查找最大的可滚动容器
            document.querySelectorAll('div').forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.overflowY === 'auto' || style.overflowY === 'scroll' ||
                    style.overflow === 'auto' || style.overflow === 'scroll') {
                    const rect = el.getBoundingClientRect();
                    const scrollHeight = el.scrollHeight;
                    // 找一个高度较大且不是侧边栏的容器
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

            // 方法2: 如果没找到，尝试通过 class 名称查找
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

            // 方法3: 查找 body 下直接子元素的最大容器
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
        }'''

        container_info = article_page.evaluate(find_scroll_container_js)
        print(f"  容器信息: {container_info}")

        # 步骤5: 滚动加载所有内容 - 滚动找到的容器
        print("滚动加载完整内容...")

        scroll_js = '''() => {
            // 首先尝试查找最大的可滚动容器
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
                // 降级: 使用 window
                window.scrollTo(0, document.body.scrollHeight);
                return { method: 'window', scrollHeight: document.body.scrollHeight };
            }

            // 滚动找到的容器
            const finalHeight = scrollContainer.scrollHeight;
            let scrolled = 0;
            const scrollStep = window.innerHeight;

            while (scrolled < finalHeight) {
                scrollContainer.scrollTop += scrollStep;
                scrolled += scrollStep;
                // 等待一小段时间让内容加载
                if (typeof requestAnimationFrame === 'function') {
                    requestAnimationFrame(() => {});
                }
            }

            // 滚动回顶部
            scrollContainer.scrollTop = 0;

            return {
                method: 'container',
                containerClass: scrollContainer.className,
                scrollHeight: finalHeight
            };
        }'''

        scroll_result = article_page.evaluate(scroll_js)
        print(f"  滚动结果: {scroll_result}")
        article_page.wait_for_timeout(2000)

        # 获取最终页面高度
        final_height = article_page.evaluate("document.documentElement.scrollHeight")
        print(f"页面总高度: {final_height}px")

        # 滚动回顶部
        article_page.evaluate("window.scrollTo(0, 0)")
        article_page.wait_for_timeout(1000)

        # 步骤6: 设置足够大的视口
        viewport_width = 1920
        viewport_height = max(final_height, 4000)
        print(f"设置视口: {viewport_width} x {viewport_height}")
        article_page.set_viewport_size({"width": viewport_width, "height": viewport_height})
        article_page.wait_for_timeout(2000)

        # 步骤6.5: 再次确保内容区域扩展到全屏
        print("确保内容区域全屏显示...")
        expand_content_js = '''() => {
            // 找到 Index_contentWrap 并扩展
            const contentEl = document.querySelector('[class*="Index_contentWrap"]');
            if (contentEl) {
                contentEl.style.position = 'absolute';
                contentEl.style.left = '0';
                contentEl.style.top = '0';
                contentEl.style.width = '1920px';
                contentEl.style.height = '100%';
                contentEl.style.maxWidth = 'none';
                contentEl.style.zIndex = '100';

                // 找到内部滚动容器并扩展
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

            // 备选：直接扩展 body 下的直接子元素
            document.body.querySelectorAll(':scope > div').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.left < 100 && rect.width < 1000) {
                    el.style.position = 'absolute';
                    el.style.left = '0';
                    el.style.width = '1920px';
                }
            });

            return { expanded: false };
        }'''

        expand_content_result = article_page.evaluate(expand_content_js)
        print(f"  内容区域扩展结果: {expand_content_result}")
        article_page.wait_for_timeout(1000)

        # 步骤7: 展开内容容器到完整高度并获取高度
        print("展开内容容器到完整高度...")

        # 先滚动到容器底部加载所有内容，同时获取 scrollHeight
        get_and_expand_js = '''() => {
            // 找到滚动容器
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

            // 记录当前 scrollHeight
            const originalScrollHeight = scrollContainer.scrollHeight;

            // 滚动到最底部加载所有内容
            scrollContainer.scrollTop = originalScrollHeight;
            // 等待一下让内容加载
            const loadedScrollHeight = scrollContainer.scrollHeight;

            // 滚动回顶部
            scrollContainer.scrollTop = 0;

            // 展开容器 - 直接设置很大的高度
            scrollContainer.style.maxHeight = 'none';
            scrollContainer.style.height = (loadedScrollHeight + 500) + 'px';
            scrollContainer.style.overflow = 'visible';

            // 禁用 simplebar
            const parent = scrollContainer.parentElement;
            if (parent && (parent.className.includes('simplebar') || parent.className.includes('SimpleBar'))) {
                parent.style.maxHeight = 'none';
                parent.style.height = (loadedScrollHeight + 500) + 'px';
                parent.style.overflow = 'visible';
                // 尝试禁用 simplebar 的滚动功能
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
        }'''

        expand_result = article_page.evaluate(get_and_expand_js)
        print(f"  展开结果: {expand_result}")
        article_page.wait_for_timeout(2000)

        # 步骤8: 生成 PDF - 使用 A3 页面尺寸和扩展的内容宽度
        content_height = expand_result.get('loadedScrollHeight', 25000)
        # 使用 1920px 宽度（与视口一致）
        pdf_width = 1920
        print(f"正在生成 PDF (A3版面, 宽度: {pdf_width}px, 内容高度: {content_height}px)...")
        # A3: 297mm x 420mm
        # 使用 px 作为单位，1920px 约等于 508mm（超过 A3 宽度）
        # Playwright PDF 使用 mm 或直接 px
        article_page.pdf(
            path=str(output_path),
            width=f"{pdf_width}px",
            height=f"{content_height}px",
            print_background=True,
            margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"}
        )

        # 关闭文章页面
        article_page.close()

        # 保持登录页面打开以便后续使用（或可以关闭）
        # browser.close()  # 不关闭浏览器，让用户可以继续操作

    print(f"\nPDF 已保存: {output_path}")
    return 0


def save_page(args):
    """Save a page as PDF using saved cookie."""
    cookie = None

    if args.cookie:
        cookie = args.cookie
    elif args.use_config or args.use_chrome:
        cookie = get_cookie()
        if not cookie:
            print("错误: 没有保存的 Cookie，请先登录")
            return 1
    else:
        cookie = get_cookie()

    if not cookie:
        print("错误: 没有可用的 Cookie")
        return 1

    if not args.url:
        print("错误: URL 是必需的")
        return 1

    output_dir = args.output or get_default_output_dir()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_name = args.name or "geekbang_article"
    output_path = output_dir / f"{output_name}.pdf"

    try:
        print(f"正在生成 PDF: {output_path}")
        convert_with_cookie(args.url, cookie, output_path, options={
            "page_size": args.page_size,
            "landscape": args.landscape
        })
        print(f"PDF 保存成功: {output_path}")
        return 0
    except Exception as e:
        print(f"生成 PDF 失败: {e}")
        return 1


def main():
    """Main entry point."""
    args = parse_args()

    if args.login:
        return handle_login(args)

    if args.set_default_dir:
        output_dir = Path(args.set_default_dir)
        if not output_dir.is_dir():
            print(f"错误: 目录不存在: {output_dir}")
            return 1
        set_default_output_dir(str(output_dir))
        print(f"默认输出目录已设置为: {output_dir}")
        return 0

    if args.browser_login:
        return browser_login_and_save(args)

    if not args.url:
        print("错误: URL 是必需的")
        print("\n使用 --browser-login 模式:")
        print("  python main.py <url> --browser-login")
        return 1

    return save_page(args)


if __name__ == "__main__":
    sys.exit(main())
