# CLAUDE.md

GeekBang PDF Saver - CLI 工具，将极客时间课程页面保存为 PDF。

## 常用命令

```bash
./install.sh              # 安装依赖
./run.sh                  # 交互式输入 URL
./run.sh <url>           # 下载单篇文章
./run.sh --batch         # 批量下载（urls_batch.txt）
python3 main.py <url> --browser-login  # 首次使用引导登录
python3 main.py <url> --use-config     # 使用已保存 Cookie
```

## 项目结构

```
src/
├── core/          # auth.py, fetcher.py, parser.py, converter.py, exceptions.py
├── cli/           # commands.py, formatters.py
├── models/        # config.py, pdf_options.py
└── utils/         # constants.py, javascript.py, logging_config.py, waits.py
config/
├── config.py      # 配置文件管理
└── selectors.json # 网站选择器配置
scripts/           # JavaScript 脚本（内容处理）
```

## 核心实现

### PDF 生成流程
1. 打开登录页面 → 用户完成登录
2. 在新标签页打开目标 URL
3. 移除浮层、隐藏侧边栏
4. 滚动加载完整内容（极客时间是 SPA）
5. 展开内容容器到完整高度
6. 生成 PDF（full_page=True）

### 关键技术点
- `simplebar-content-wrapper` - 内容滚动容器
- `Index_side` - 侧边栏元素
- `sync_playwright()` - 无头浏览器启动
- Cookie 无效时自动跳转登录

## 代码规范

- 类型提示必须使用（type hints）
- 异常继承自 `GeekBangError` 基类
- 配置文件存储在项目 `config/` 目录

## 调试指南

1. **Cookie 无效**：自动弹出浏览器引导登录
2. **内容未加载**：检查 SPA 滚动容器是否正确展开
3. **PDF 不完整**：确认内容容器高度已展开到完整高度

## 重要提示

- 极客时间是 SPA，内容需要 JavaScript 渲染
- 文章内容使用 `simplebar` 滚动库
- PDF 生成使用 `full_page=True` 模式

## 持续改进

**每次修复问题后，将教训写入 CLAUDE.md**。

示例：在对话末尾添加 "Update your CLAUDE.md so you don't make that mistake again"

文件应像代码一样被重构、审查、持续改进。
