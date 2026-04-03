#!/bin/bash

# GeekBang PDF 保存工具 - 安装脚本
#
# 用法:
#   ./install.sh          运行安装
#   ./install.sh --help   显示帮助

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

show_help() {
    echo "用法:"
    echo "  ./install.sh          运行安装"
    echo "  ./install.sh --help   显示帮助"
    echo ""
    echo "安装内容:"
    echo "  - Python 依赖 (pip install -r requirements.txt)"
    echo "  - Node.js 依赖 (npm install)"
    echo "  - Playwright 浏览器驱动"
}

install_python_deps() {
    echo "[1/3] 安装 Python 依赖..."
    if command -v pip &> /dev/null; then
        pip install -r requirements.txt
    elif command -v pip3 &> /dev/null; then
        pip3 install -r requirements.txt
    else
        echo "错误: 未找到 pip，请先安装 Python"
        exit 1
    fi
    echo "Python 依赖安装完成"
}

install_nodejs_deps() {
    echo "[2/3] 安装 Node.js 依赖..."
    if ! command -v npm &> /dev/null; then
        echo "警告: 未找到 npm，跳过 Node.js 依赖安装"
        return
    fi
    npm install
    echo "Node.js 依赖安装完成"
}

install_playwright_browser() {
    echo "[3/3] 安装 Playwright 浏览器驱动..."
    if ! command -v npx &> /dev/null; then
        echo "警告: 未找到 npx，跳过 Playwright 安装"
        return
    fi
    npx playwright install chromium
    echo "Playwright 浏览器驱动安装完成"
}

main() {
    case "${1:-}" in
        -h|--help)
            show_help
            ;;
        "")
            echo "=== GeekBang PDF 保存工具安装 ==="
            echo ""
            install_python_deps
            echo ""
            install_nodejs_deps
            echo ""
            install_playwright_browser
            echo ""
            echo "=== 安装完成 ==="
            echo ""
            echo "启动脚本: ./run.sh"
            echo ""
            echo "使用方式:"
            echo "  ./run.sh                 交互式菜单"
            echo "  ./run.sh <url>          下载单篇文章"
            echo "  ./run.sh --batch        批量下载"
            echo "  ./run.sh --login        浏览器登录"
            echo "  ./run.sh -h             显示帮助"
            ;;
        *)
            echo "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
