# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

GeekBang PDF Saver - CLI tool to save geekbang.org course pages as PDF files with full content rendering.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Run
python main.py <url> -o ./output --use-chrome

# Options:
#   --use-chrome       Use existing Chrome session for authentication
#   -o, --output       Output directory
#   -n, --name         Output filename
#   --page-size        PDF page size (A4, Letter, Legal)
#   --landscape        Use landscape orientation
```

## Architecture

```
geekbang-pdf/
├── main.py              # CLI entry point
├── src/
│   ├── __init__.py
│   ├── auth.py          # Selenium login / Chrome session
│   ├── fetcher.py       # HTTP page fetching
│   ├── parser.py        # HTML parsing (for static pages)
│   ├── converter.py      # Puppeteer PDF generation
│   └── exceptions.py     # Custom exceptions
├── config/
│   └── config.py        # Config file management (~/.geekbang-pdf/)
├── requirements.txt     # Python dependencies
└── package.json        # Node.js dependencies (Puppeteer)
```

## Key Implementation Details

### Chrome Session Authentication
- Requires Chrome running with remote debugging port 28800
- Cookie extraction via Selenium CDP connection to existing Chrome session
- Cookies are encrypted in Chrome's SQLite database, must get from running instance

### PDF Generation
- Uses Puppeteer to connect to existing Chrome session
- Generates PDF directly from rendered page content
- Supports SPA (Single Page Application) pages with JavaScript-rendering

### Important Notes
- geekbang.org pages are SPA - content requires JavaScript rendering
- Cookies cannot be read directly from Chrome's SQLite (encrypted)
- Must use `--use-chrome` flag with an already logged-in Chrome session
- Chrome must be running with: `--remote-debugging-port=28800`
