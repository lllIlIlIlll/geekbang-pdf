"""
诊断问题的辅助函数

用法：python3 helper.py <issue_type>
类型：pdf_blank, login_failed, content_truncate
"""

import json
import subprocess
import sys
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
    except json.JSONDecodeError as e:
        return {'status': 'error', 'message': f'Cookie 格式错误: {e}'}
    except PermissionError:
        return {'status': 'error', 'message': '无读取权限'}
    except Exception as e:
        return {'status': 'error', 'message': f'读取失败: {e}'}


def _check_auth() -> dict:
    """检查认证状态"""
    try:
        result = subprocess.run(
            ['python3', '-c', '''
import sys
sys.path.insert(0, ".")
from config import get_cookie
cookie = get_cookie()
print("OK" if cookie else "NO_COOKIE")
'''],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return {'status': 'error', 'message': result.stderr.strip() or '认证检查失败'}
        output = result.stdout.strip()
        if output == 'OK':
            return {'status': 'ok', 'message': 'Cookie 存在，认证可用'}
        return {'status': 'error', 'message': 'Cookie 不存在或已过期'}
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'message': '认证检查超时'}
    except FileNotFoundError:
        return {'status': 'error', 'message': 'Python3 未找到'}
    except Exception as e:
        return {'status': 'error', 'message': f'认证检查异常: {e}'}


def _check_selectors() -> dict:
    """检查选择器配置"""
    selectors_path = Path('config/selectors.json')
    if not selectors_path.exists():
        return {'status': 'error', 'message': 'selectors.json 不存在'}

    try:
        with open(selectors_path) as f:
            selectors = json.load(f)
        return {'status': 'ok', 'message': f'选择器配置正常，共 {len(selectors)} 个选择器', 'data': selectors}
    except json.JSONDecodeError as e:
        return {'status': 'error', 'message': f'选择器 JSON 格式错误: {e}'}
    except PermissionError:
        return {'status': 'error', 'message': '无读取权限'}
    except Exception as e:
        return {'status': 'error', 'message': f'读取失败: {e}'}


def _check_general() -> dict:
    """未知类型的 fallback — 明确提示不支持"""
    return {'status': 'warning', 'message': '不支持的诊断类型，请手动排查'}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 helper.py <issue_type>")
        print("Types: pdf_blank, login_failed, content_truncate")
        sys.exit(1)
    _type = sys.argv[1]
    result = diagnose_issue(_type)
    print(json.dumps(result, ensure_ascii=False, indent=2))
