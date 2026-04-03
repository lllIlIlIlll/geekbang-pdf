"""
诊断问题的辅助函数
"""

import subprocess
import json
from pathlib import Path


def diagnose_issue(issue_type: str) -> dict:
    """
    根据问题类型进行诊断

    Args:
        issue_type: 问题类型 (pdf_blank, login_failed, etc)

    Returns:
        诊断结果字典
    """
    diagnoses = {
        'pdf_blank': _check_cookie,
        'login_failed': _check_auth,
        'content_truncate': _check_selectors,
    }

    checker = diagnoses.get(issue_type, _check_general)
    return checker()


def _check_cookie() -> dict:
    """检查 Cookie 状态"""
    config_path = Path('config/cookie.json')
    if not config_path.exists():
        return {'status': 'error', 'message': 'Cookie 配置文件不存在'}

    try:
        with open(config_path) as f:
            cookie = json.load(f)
        return {
            'status': 'ok',
            'message': f'Cookie 存在，共 {len(cookie)} 条',
            'data': cookie
        }
    except Exception as e:
        return {'status': 'error', 'message': f'Cookie 解析失败: {e}'}


def _check_auth() -> dict:
    """检查认证状态"""
    result = subprocess.run(
        ['python3', '-c', 'from src.core.auth import check_auth; print(check_auth())'],
        capture_output=True,
        text=True
    )
    return {'status': 'ok' if result.returncode == 0 else 'error', 'message': result.stdout}


def _check_selectors() -> dict:
    """检查选择器配置"""
    selectors_path = Path('config/selectors.json')
    if not selectors_path.exists():
        return {'status': 'error', 'message': 'selectors.json 不存在'}

    try:
        with open(selectors_path) as f:
            selectors = json.load(f)
        return {'status': 'ok', 'message': '选择器配置正常', 'data': selectors}
    except Exception as e:
        return {'status': 'error', 'message': f'选择器解析失败: {e}'}


def _check_general() -> dict:
    """通用检查"""
    return {'status': 'ok', 'message': '未知的诊断类型'}
