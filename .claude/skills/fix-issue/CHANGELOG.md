# Changelog

## 2.0.0 (2026-04-03)

- 重构 SKILL.md：增加 Checklist、一键启动 Prompt 前移、统一祈使句语态
- Frontmatter 补充触发词：异常、不工作、挂了、broken、crash、not working
- 修复脚本导入路径：`scripts.helper` → `.claude/skills/fix-issue/scripts/helper.py`
- 修复 `_validate_general` 和 `_check_general` 的 fallback 返回值（不再误报成功）
- 脚本增加 `__main__` CLI 入口，支持直接命令行调用
- 声明外部依赖 pdfinfo
- 修复 Hook 配置示例中的非法 JSON 注释
- EXAMPLES.md 重写为 3 个差异化场景（明确报错 / 间歇性故障 / 无报错行为异常）
- REFERENCE.md 重写为完整参考手册（诊断命令 / 问题速查 / 文件索引）
- templates/report.md 与 Phase 3 变更摘要格式对齐

## 1.0.0 (2026-03-01)

- 初始版本
- 5-Phase 修复流程（复现 → AC → 修复 → 验证 → CLAUDE.md）
- 诊断脚本 helper.py / validator.py
- AC 模板、反模式速查、Hook 配置模板
