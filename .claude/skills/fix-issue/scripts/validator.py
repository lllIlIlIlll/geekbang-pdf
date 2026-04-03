"""
验证修复结果的函数
"""

import subprocess
from pathlib import Path


def validate_fix(fix_type: str, target: str = None) -> dict:
    """
    验证修复结果

    Args:
        fix_type: 修复类型 (cookie, selector, etc)
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
    result = subprocess.run(
        ['python3', '-c', 'from src.core.auth import validate_cookie; print(validate_cookie())'],
        capture_output=True,
        text=True
    )
    success = result.returncode == 0 and 'True' in result.stdout
    return {
        'valid': success,
        'message': 'Cookie 有效' if success else 'Cookie 无效'
    }


def _validate_selector(target=None) -> dict:
    """验证选择器修复"""
    if not target:
        return {'valid': False, 'message': '未指定选择器目标'}

    result = subprocess.run(
        ['python3', '-c', f'from config.selectors import test; print(test("{target}"))'],
        capture_output=True,
        text=True
    )
    return {
        'valid': result.returncode == 0,
        'message': result.stdout.strip()
    }


def _validate_pdf(target=None) -> dict:
    """验证 PDF 生成"""
    if not target:
        return {'valid': False, 'message': '未指定 PDF 目标'}

    pdf_path = Path(target)
    if not pdf_path.exists():
        return {'valid': False, 'message': f'PDF 文件不存在: {target}'}

    result = subprocess.run(
        ['pdfinfo', target],
        capture_output=True,
        text=True
    )
    return {
        'valid': result.returncode == 0,
        'message': f'PDF 页面数: {len([l for l in result.stdout.splitlines() if "Pages:" in l])}'
    }


def _validate_general(target=None) -> dict:
    """通用验证"""
    return {'valid': True, 'message': '验证通过'}
