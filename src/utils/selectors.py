"""Platform-specific CSS selectors loader."""

import json
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_SELECTORS = {
    "article_content": ["article", "main", ".content", ".post-content"],
    "scroll_container": ["[class*='content']", "[class*='article']"],
    "sidebar": [],
    "fixed_elements": {
        "classnames": ["modal", "popup", "overlay"],
        "texts": ["登录", "注册", "推荐试读", "仅针对订阅"]
    },
    "exclude_classes": ["sidebar", "catalog", "menu", "nav", "list"]
}


def get_selectors_path() -> Path:
    """获取 selectors.json 路径"""
    return Path(__file__).parent.parent.parent / "config" / "selectors.json"


def load_selectors(platform: str = "geekbang") -> Dict:
    """加载指定平台的选择器配置

    Args:
        platform: 平台标识符 (如 "geekbang", "dedao", "zhihu")

    Returns:
        包含所有选择器的字典
    """
    selectors_path = get_selectors_path()

    if selectors_path.exists():
        with open(selectors_path, "r", encoding="utf-8") as f:
            all_selectors = json.load(f)
            if platform in all_selectors:
                return all_selectors[platform]
            elif "default" in all_selectors:
                # 回退到 default 配置
                return all_selectors["default"]

    return DEFAULT_SELECTORS


def get_platform_from_url(url: str) -> str:
    """从 URL 推断平台

    Args:
        url: 页面 URL

    Returns:
        平台标识符，默认为 "geekbang"
    """
    url_lower = url.lower()
    if "geekbang" in url_lower:
        return "geekbang"
    elif "dedao" in url_lower:
        return "dedao"
    elif "zhihu" in url_lower:
        return "zhihu"
    # 可扩展更多平台...
    return "default"
