"""
验证修复结果的函数

用法：python3 validator.py <fix_type> [target]
类型：cookie, selector, pdf
"""

import json
import subprocess
import sys
from pathlib import Path


def validate_fix(fix_type: str, target: str = None) -> dict:
    """
    验证修复结果

    Args:
        fix_type: 修复类型 (cookie, selector, pdf)
        target: 修复目标（可选）

    Returns:
        验证结果字典
    """
    validators = {
        'cookie': _validate_cookie,
        'selector': _validate_selector,
        'pdf': _validate_pdf,
    }

    validator = validators.get(fix_type, _validate_general)
    return validator(target)


def _validate_cookie(target=None) -> dict:
    """验证 Cookie 修复"""
    try:
        result = subprocess.run(
            ['python3', '-c', '''
import sys
sys.path.insert(0, ".")
from config import get_cookie
cookie = get_cookie()
print("VALID" if cookie else "INVALID")
'''],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return {'valid': False, 'message': result.stderr.strip() or '验证失败'}
        output = result.stdout.strip()
        success = output == 'VALID'
        return {'valid': success, 'message': 'Cookie 有效' if success else 'Cookie 无效或已过期'}
    except subprocess.TimeoutExpired:
        return {'valid': False, 'message': '验证超时'}
    except FileNotFoundError:
        return {'valid': False, 'message': 'Python3 未找到'}
    except Exception as e:
        return {'valid': False, 'message': f'验证异常: {e}'}


def _validate_selector(target=None) -> dict:
    """验证选择器修复"""
    if not target:
        return {'valid': False, 'message': '未指定选择器目标'}

    try:
        result = subprocess.run(
            ['python3', '-c', f'''
import sys
import json
sys.path.insert(0, ".")
with open("config/selectors.json") as f:
    selectors = json.load(f)

# 解析目标路径（如 "geekbang.article_content"）
parts = "{target}".split(".")
current = selectors
for part in parts:
    if isinstance(current, dict) and part in current:
        current = current[part]
    else:
        print("NOT_FOUND")
        sys.exit(0)

# 检查是否有值
if current:
    print("OK:" + str(current)[:50])
else:
    print("EMPTY")
'''],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout.strip()
        if output == 'NOT_FOUND':
            return {'valid': False, 'message': f'选择器路径 "{target}" 不存在'}
        if output == 'EMPTY':
            return {'valid': False, 'message': f'选择器路径 "{target}" 为空'}
        if result.returncode != 0:
            return {'valid': False, 'message': result.stderr.strip()}
        return {'valid': True, 'message': f'选择器正常: {output}'}
    except subprocess.TimeoutExpired:
        return {'valid': False, 'message': '验证超时'}
    except FileNotFoundError:
        return {'valid': False, 'message': 'Python3 未找到'}
    except Exception as e:
        return {'valid': False, 'message': f'验证异常: {e}'}


def _validate_pdf(target=None) -> dict:
    """验证 PDF 生成"""
    if not target:
        return {'valid': False, 'message': '未指定 PDF 目标'}

    pdf_path = Path(target)
    if not pdf_path.exists():
        return {'valid': False, 'message': f'PDF 文件不存在: {target}'}

    if not pdf_path.suffix.lower() == '.pdf':
        return {'valid': False, 'message': f'不是 PDF 文件: {target}'}

    try:
        result = subprocess.run(
            ['pdfinfo', str(pdf_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return {'valid': False, 'message': 'PDF 信息读取失败'}

        # 解析页面数
        pages = 0
        for line in result.stdout.splitlines():
            if 'Pages:' in line:
                try:
                    pages = int(line.split(':')[-1].strip())
                except ValueError:
                    pass
                break

        if pages > 0:
            return {'valid': True, 'message': f'PDF 正常，页面数: {pages}'}
        return {'valid': False, 'message': '无法解析 PDF 页面数'}
    except FileNotFoundError:
        return {'valid': False, 'message': 'pdfinfo 未安装，请安装 poppler-utils'}
    except subprocess.TimeoutExpired:
        return {'valid': False, 'message': 'PDF 信息读取超时'}
    except Exception as e:
        return {'valid': False, 'message': f'验证异常: {e}'}


def _validate_general(target=None) -> dict:
    """未知类型的 fallback — 返回失败，避免误报"""
    return {'valid': False, 'message': '不支持的验证类型，请手动验证'}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 validator.py <fix_type> [target]")
        print("Types: cookie, selector, pdf")
        sys.exit(1)
    _type = sys.argv[1]
    _target = sys.argv[2] if len(sys.argv) > 2 else None
    result = validate_fix(_type, _target)
    print(json.dumps(result, ensure_ascii=False, indent=2))
