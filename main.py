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
from src.auth import login, get_cookies_from_existing_chrome
from src.fetcher import fetch_page, get_page_title
from src.parser import process_html, extract_article_content
from src.converter import convert_to_pdf, convert_url_to_pdf, convert_chrome_page_to_pdf, write_html_to_temp, cleanup_temp_files
from config.config import (
    load_config,
    save_config,
    get_cookie,
    set_cookie,
    get_default_output_dir,
    set_default_output_dir,
)


def parse_args():
    """Parse command line arguments.

    Returns:
        Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Save geekbang.org course pages as PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Login to get cookie
  python main.py --login

  # Save a course page using saved cookie
  python main.py https://time.geekbang.org/column/article/12345 -o ./output

  # Save with custom output name
  python main.py https://time.geekbang.org/column/article/12345 -n my_article -o ./output

  # Use cookie directly
  python main.py https://time.geekbang.org/column/article/12345 --cookie "abc123..."

  # Use existing Chrome session to get cookie
  python main.py https://time.geekbang.org/column/article/12345 -o ./output --use-chrome

  # Save with specific page size
  python main.py https://time.geekbang.org/column/article/12345 --page-size Letter
        """
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="GeekBang article URL to save as PDF"
    )

    parser.add_argument(
        "-o", "--output",
        metavar="DIR",
        help="Output directory for PDF file"
    )

    parser.add_argument(
        "-n", "--name",
        metavar="NAME",
        help="Output filename (without extension)"
    )

    parser.add_argument(
        "--cookie",
        metavar="COOKIE",
        help="Session cookie for authentication"
    )

    parser.add_argument(
        "--use-config",
        action="store_true",
        help="Use cookie from config file"
    )

    parser.add_argument(
        "--login",
        action="store_true",
        help="Login to geekbang.org and save cookie"
    )

    parser.add_argument(
        "--use-chrome",
        action="store_true",
        help="Get cookie from existing Chrome browser session"
    )

    parser.add_argument(
        "--chrome-profile",
        metavar="PROFILE",
        default="Default",
        help="Chrome profile name (default: Default)"
    )

    parser.add_argument(
        "--email",
        metavar="EMAIL",
        help="Email for login (use with --login)"
    )

    parser.add_argument(
        "--password",
        metavar="PASSWORD",
        help="Password for login (use with --login)"
    )

    parser.add_argument(
        "--page-size",
        choices=["A4", "Letter", "Legal"],
        default="A4",
        help="Page size for PDF (default: A4)"
    )

    parser.add_argument(
        "--landscape",
        action="store_true",
        help="Use landscape orientation"
    )

    parser.add_argument(
        "--no-download-images",
        action="store_true",
        help="Don't download images locally"
    )

    parser.add_argument(
        "--set-default-dir",
        metavar="DIR",
        help="Set default output directory in config"
    )

    return parser.parse_args()


def handle_login(args):
    """Handle login operation.

    Args:
        args: Parsed arguments

    Returns:
        int: Exit code
    """
    email = args.email
    password = args.password

    if not email or not password:
        print("Error: --email and --password are required for login")
        return 1

    try:
        print(f"Logging in as {email}...")
        cookie = login(email, password)
        set_cookie(cookie)
        print("Login successful! Cookie saved to config.")
        return 0
    except AuthError as e:
        print(f"Login failed: {e}")
        return 1


def save_page(args):
    """Save a page as PDF.

    Args:
        args: Parsed arguments

    Returns:
        int: Exit code
    """
    # Determine cookie to use
    cookie = None
    if args.cookie:
        cookie = args.cookie
    elif args.use_config:
        cookie = get_cookie()
        if not cookie:
            print("Error: No cookie found in config. Please login first.")
            return 1
    elif args.use_chrome:
        try:
            print("Getting cookie from Chrome...")
            cookie = get_cookies_from_existing_chrome(debugging_port=28800)
            print("Successfully obtained cookie from Chrome")
        except AuthError as e:
            print(f"Failed to get cookie from Chrome: {e}")
            return 1
    else:
        # Try to use cookie from config
        cookie = get_cookie()

    if not cookie:
        print("Error: No cookie provided. Use --cookie, --use-config, --use-chrome, or login first.")
        print("Run with --login to authenticate.")
        return 1

    # Validate URL
    if not args.url:
        print("Error: URL is required")
        return 1

    # Determine output directory
    output_dir = args.output or get_default_output_dir()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Determine output filename
        if args.name:
            output_name = args.name
        else:
            # Use a generic name first, will rename after getting title
            output_name = "geekbang_article"

        output_path = output_dir / f"{output_name}.pdf"

        # For SPA pages, use existing Chrome session to get page content
        print(f"Converting page from existing Chrome session to PDF...")
        print("(Using your already logged-in session)")

        convert_chrome_page_to_pdf(
            28800,  # Chrome debugging port
            output_path,
            options={
                "page_size": args.page_size,
                "landscape": args.landscape,
            }
        )

        # Get title from generated PDF or use the filename
        print(f"PDF saved successfully: {output_path}")
        return 0

    except URLInvalidError as e:
        print(f"Invalid URL: {e}")
        return 1
    except FetchError as e:
        print(f"Failed to fetch page: {e}")
        return 1
    except ConversionError as e:
        print(f"Failed to convert to PDF: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    finally:
        # Cleanup temp files
        if "temp_html" in locals():
            cleanup_temp_files(temp_html)


def set_default_directory(args):
    """Set default output directory.

    Args:
        args: Parsed arguments

    Returns:
        int: Exit code
    """
    if not args.set_default_dir:
        return 0

    output_dir = Path(args.set_default_dir)
    if not output_dir.is_dir():
        print(f"Error: Directory does not exist: {output_dir}")
        return 1

    set_default_output_dir(str(output_dir))
    print(f"Default output directory set to: {output_dir}")
    return 0


def main():
    """Main entry point."""
    args = parse_args()

    # Handle login
    if args.login:
        return handle_login(args)

    # Handle set default directory
    exit_code = set_default_directory(args)
    if args.set_default_dir:
        return exit_code

    # If no URL provided, show help
    if not args.url:
        print("Error: URL is required. Use --help for usage information.")
        return 1

    # Save page as PDF
    return save_page(args)


if __name__ == "__main__":
    sys.exit(main())
