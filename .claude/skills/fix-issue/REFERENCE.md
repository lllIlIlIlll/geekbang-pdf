# Fix Issue 参考手册

诊断命令、常见问题速查、调试技巧。

---

## 前置依赖

| 工具 | 用途 | 安装 |
|------|------|------|
| Python 3.8+ | 运行诊断脚本 | 系统自带或 `brew install python3` |
| pdfinfo | PDF 验证 | macOS: `brew install poppler` / Linux: `apt install poppler-utils` |

---

## 诊断脚本

脚本位于 `.claude/skills/fix-issue/scripts/`，从项目根目录运行。

### 问题诊断（helper.py）

```bash
# Cookie / PDF 空白问题
python3 .claude/skills/fix-issue/scripts/helper.py pdf_blank

# 登录 / 认证问题
python3 .claude/skills/fix-issue/scripts/helper.py login_failed

# 内容截断 / 选择器问题
python3 .claude/skills/fix-issue/scripts/helper.py content_truncate
```

输出格式：

```json
{
  "status": "ok | error | warning",
  "message": "诊断结果描述",
  "data": {}
}
```

### 修复验证（validator.py）

```bash
# 验证 Cookie 修复
python3 .claude/skills/fix-issue/scripts/validator.py cookie

# 验证 PDF 生成（需指定文件路径）
python3 .claude/skills/fix-issue/scripts/validator.py pdf out/test.pdf

# 验证选择器（需指定选择器路径，如 article_title）
python3 .claude/skills/fix-issue/scripts/validator.py selector article_title
```

输出格式：

```json
{
  "valid": true,
  "message": "验证结果描述"
}
```

---

## 常见问题速查

### PDF 生成问题

| 现象 | 可能原因 | 排查入口 |
|------|----------|----------|
| PDF 空白 / 0 字节 | Cookie 过期 | `helper.py pdf_blank` → `src/core/auth.py` |
| 内容截断 | 滚动容器未完全展开 | `helper.py content_truncate` → `src/core/converter.py` |
| 样式丢失 | CSS 未加载 / 页面未渲染完成 | 检查 `scripts/` 目录下 JS 脚本 |
| 包含多余 UI 元素 | 选择器未正确隐藏浮层 | `config/selectors.json` |

### 登录与认证问题

| 现象 | 可能原因 | 排查入口 |
|------|----------|----------|
| 登录失败 | Cookie 文件损坏 / 路径错误 | `helper.py login_failed` → `config/config.py` |
| 重定向循环 | 登录检测选择器失配 | `config/selectors.json` 中登录相关选择器 |
| 登录超时 | 等待时间不足 / 页面加载慢 | `src/core/auth.py` 超时配置 |

### 批量下载问题

| 现象 | 可能原因 | 排查入口 |
|------|----------|----------|
| 中途中断 | 限流 / 网络超时 | `src/core/fetcher.py` 重试逻辑 |
| 部分 URL 跳过 | urls_batch.txt 格式错误 | 检查文件编码和换行符 |
| 重复下载 | 无断点续传 | 检查是否有已下载文件检测逻辑 |

---

## 手动调试命令

```bash
# 查看详细日志
python3 main.py <url> --verbose

# 首次登录（浏览器引导）
python3 main.py <url> --browser-login

# 使用已保存 Cookie
python3 main.py <url> --use-config

# 检查 Cookie 文件内容
python3 -c "import json; print(json.dumps(json.load(open('config/cookie.json')), indent=2))"

# 检查选择器配置
python3 -c "import json; print(json.dumps(json.load(open('config/selectors.json')), indent=2))"
```

---

## 修复报告模板

完成修复后可用此模板归档完整记录 → **[templates/report.md](templates/report.md)**

---

## 相关文件索引

| 文件 | 职责 |
|------|------|
| `src/core/auth.py` | 认证、登录、Cookie 管理 |
| `src/core/fetcher.py` | HTTP 请求、重试 |
| `src/core/parser.py` | 页面解析 |
| `src/core/converter.py` | PDF 生成、页面滚动、内容展开 |
| `src/core/exceptions.py` | 项目异常类层次 |
| `config/config.py` | 配置文件管理 |
| `config/selectors.json` | 页面选择器配置 |
| `scripts/` | JavaScript 脚本（DOM 操作、内容处理） |
