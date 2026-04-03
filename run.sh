#!/bin/bash

# GeekBang PDF 保存工具 - 交互式启动脚本
#
# 用法:
#   run.sh <url>           下载单篇文章
#   run.sh --batch         批量下载（使用 urls_batch.txt）
#   run.sh --login         浏览器登录
#   run.sh                 交互式输入 URL

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 优先使用 python3，回退到 python
PYTHON_CMD=$(command -v python3 || command -v python)

download_single() {
    local url="$1"
    if [ -z "$url" ]; then
        echo "错误: URL 不能为空"
        exit 1
    fi
    echo "使用已保存 Cookie 下载文章: $url"
    $PYTHON_CMD main.py "$url" --use-config
}

download_batch() {
    if [ ! -f "$SCRIPT_DIR/urls_batch.txt" ]; then
        echo "错误: urls_batch.txt 文件不存在"
        exit 1
    fi
    echo "批量下载文章（使用 urls_batch.txt）..."
    local count=0
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        ((count++))
        echo "[$count] 下载: $line"
        $PYTHON_CMD main.py "$line" --use-config
    done < "$SCRIPT_DIR/urls_batch.txt"
    echo "批量下载完成，共 $count 篇"
}

browser_login() {
    echo "启动浏览器登录..."
    $PYTHON_CMD main.py --browser-login
}

show_url_input() {
    echo ""
    echo "=== GeekBang PDF 保存工具 ==="
    read -p "请输入文章 URL: " url
    if [ -n "$url" ]; then
        download_single "$url"
    else
        echo "URL 不能为空"
        exit 1
    fi
}

show_help() {
    echo "用法:"
    echo "  run.sh <url>           下载单篇文章"
    echo "  run.sh --batch         批量下载（使用 urls_batch.txt）"
    echo "  run.sh --login         浏览器登录"
    echo "  run.sh                 交互式输入 URL"
}

# 命令行参数处理
case "${1:-}" in
    --login)
        browser_login
        ;;
    --batch)
        download_batch
        ;;
    -h|--help)
        show_help
        ;;
    "")
        show_url_input
        ;;
    *)
        download_single "$1"
        ;;
esac
