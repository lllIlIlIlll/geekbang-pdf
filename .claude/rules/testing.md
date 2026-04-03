# 测试规范

## 单元测试

- 使用 `pytest` 框架
- 测试文件放在 `tests/unit/` 目录
- 命名规范：`test_<模块名>.py`

## 测试原则

- 每个功能模块应有对应测试
- 测试之间相互独立
- 使用 `conftest.py` 共享 fixtures
