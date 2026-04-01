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
from src.auth import login
from src.converter import convert_with_cookie, convert_with_context
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

  # 处理多个 URL（共享登录会话）
  python main.py <url1> <url2> <url3> --browser-login

  # 从文件读取额外 URL
  python main.py <url1> --urls-file urls.txt --browser-login

  # 使用已保存的 Cookie
  python main.py <url> --use-config
        """
    )

    parser.add_argument("url", nargs="+", help="极客时间文章 URL（支持多个）")
    parser.add_argument("--urls-file", metavar="FILE", help="从文件读取额外 URL（每行一个）")
    parser.add_argument("-o", "--output", metavar="DIR", help="PDF 输出目录")
    parser.add_argument("-n", "--name", metavar="NAME", help="输出文件名（用于单 URL 模式）")
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


def read_urls_from_file(filepath):
    """Read URLs from a file (one URL per line).

    Args:
        filepath: Path to the file containing URLs

    Returns:
        list: List of URLs (empty lines and comments are skipped)
    """
    urls = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    urls.append(line)
    except Exception as e:
        print(f"读取 URL 文件失败: {e}")
    return urls


def login_and_get_context(urls):
    """Login and return browser context for shared session.

    This function:
    1. Opens login page in a new tab
    2. Waits for user to login manually
    3. Returns the browser context for processing multiple URLs

    Args:
        urls: List of URLs to process (used for saving cookies)

    Returns:
        tuple: (context, cookie_str) on success, (None, None) on failure
    """
    print("\n" + "="*50)
    print("极客时间 PDF 生成器")
    print("="*50)
    print()
    print("请在浏览器中完成以下步骤:")
    print("1. 登录极客时间")
    print("2. 登录成功后，在终端按 Enter 键继续")
    print()

    p = sync_playwright().start()
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

    # 保存 Cookie
    cookies = context.cookies()
    gb_cookies = [c for c in cookies if 'geekbang' in c.get('domain', '').lower()]
    cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in gb_cookies])
    if cookie_str:
        set_cookie(cookie_str)
        print(f"Cookie 已保存 (长度: {len(cookie_str)})")

    # 关闭登录页面
    page.close()

    return context, cookie_str, p


def browser_login_and_save(args):
    """Browser login then navigate to URL and save as PDF.

    This function handles multiple URLs with shared login session:
    1. Opens login page and waits for user to login
    2. Keeps the browser context for processing multiple URLs
    3. Processes each URL in sequence
    4. Closes the browser when all URLs are processed
    """
    # Collect all URLs
    urls = list(args.url)  # Start with command line URLs

    # Add URLs from file if specified
    if args.urls_file:
        file_urls = read_urls_from_file(args.urls_file)
        urls.extend(file_urls)
        print(f"从文件读取了 {len(file_urls)} 个 URL")

    if not urls:
        print("错误: 至少需要提供一个 URL")
        return 1

    print(f"\n待处理的 URL 数量: {len(urls)}")

    # Determine output directory
    output_dir = args.output or get_default_output_dir()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get PDF options
    pdf_options = {
        "page_size": args.page_size,
        "landscape": args.landscape
    }

    # Login and get browser context
    context, cookie_str, playwright_instance = login_and_get_context(urls)

    if context is None:
        print("登录失败，无法继续")
        return 1

    # Process all URLs
    print(f"\n开始处理 {len(urls)} 个 URL...")
    print("="*50)

    successful_urls = []
    failed_urls = []

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] 正在处理: {url}")

        try:
            output_name = None
            if args.name and len(urls) == 1:
                # Only use --name flag for single URL mode
                output_name = args.name

            output_path = output_dir / f"{output_name or 'geekbang_article'}.pdf"

            convert_with_context(
                url=url,
                context=context,
                output_path=output_path,
                options=pdf_options
            )

            print(f"  PDF 已保存: {output_path}")
            successful_urls.append(url)

        except Exception as e:
            print(f"  处理失败: {e}")
            failed_urls.append(url)

    # Close browser
    context.browser.close()
    playwright_instance.stop()

    # Print summary
    print("\n" + "="*50)
    print("处理完成!")
    print(f"成功: {len(successful_urls)}, 失败: {len(failed_urls)}")

    if failed_urls:
        print("\n失败的 URL:")
        for url in failed_urls:
            print(f"  - {url}")
        return 1

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

    # Collect all URLs
    urls = list(args.url)

    # Add URLs from file if specified
    if args.urls_file:
        file_urls = read_urls_from_file(args.urls_file)
        urls.extend(file_urls)
        print(f"从文件读取了 {len(file_urls)} 个 URL")

    if not urls:
        print("错误: 至少需要提供一个 URL")
        return 1

    output_dir = args.output or get_default_output_dir()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_options = {
        "page_size": args.page_size,
        "landscape": args.landscape
    }

    print(f"\n待处理的 URL 数量: {len(urls)}")

    successful_urls = []
    failed_urls = []

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] 正在处理: {url}")

        output_name = None
        if args.name and len(urls) == 1:
            output_name = args.name

        output_path = output_dir / f"{output_name or 'geekbang_article'}.pdf"

        try:
            convert_with_cookie(url, cookie, output_path, options=pdf_options)
            print(f"  PDF 保存成功: {output_path}")
            successful_urls.append(url)
        except Exception as e:
            print(f"  处理失败: {e}")
            failed_urls.append(url)

    # Print summary
    print("\n" + "="*50)
    print("处理完成!")
    print(f"成功: {len(successful_urls)}, 失败: {len(failed_urls)}")

    if failed_urls:
        print("\n失败的 URL:")
        for url in failed_urls:
            print(f"  - {url}")
        return 1

    return 0


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

    return save_page(args)


if __name__ == "__main__":
    sys.exit(main())
