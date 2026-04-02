# GeekBang PDF Saver

极客时间课程页面 PDF 保存工具 - 将极客时间课程页面保存为 PDF 文件，支持完整的 JavaScript 渲染内容。

## 功能特性

- **浏览器登录认证** - 自动弹出浏览器引导登录，无需手动获取 Cookie
- **完整内容保存** - 支持 SPA 单页应用，完整保存 JavaScript 动态渲染内容
- **自动滚动加载** - 自动滚动页面加载所有内容
- **隐藏界面元素** - 自动隐藏左侧导航栏、浮层等非内容元素
- **Cookie 自动保存** - 登录成功后自动保存 Cookie，下次无需重复登录
- **多页面格式支持** - 支持 A4、Letter、Legal 等多种页面尺寸
- **配置化平台支持** - CSS 选择器从 `selectors.json` 读取，支持多平台扩展

## 安装

```bash
# 克隆项目
git clone https://github.com/lllIlIlIlll/geekbang-pdf.git
cd geekbang-pdf

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Node.js 依赖（Playwright）
npm install

# 安装 Playwright 浏览器驱动
npx playwright install chromium
```

## 快速开始

```bash
# 推荐：首次使用，自动弹出浏览器引导登录
python main.py <url> --browser-login

# 示例：保存课程文章
python main.py https://time.geekbang.org/column/article/944525 --browser-login

# 指定输出目录
python main.py <url> --browser-login -o ./output

# 使用已保存的 Cookie（无需再次登录）
python main.py <url> --use-config
```

## 命令行选项

| 选项 | 说明 |
|------|------|
| `url` | 极客时间文章 URL（必需） |
| `-o, --output DIR` | PDF 输出目录 |
| `-n, --name NAME` | 输出文件名 |
| `--browser-login` | 自动弹出浏览器引导登录（推荐首次使用） |
| `--cookie COOKIE` | 直接提供 Cookie 字符串 |
| `--use-config` | 使用配置文件中已保存的 Cookie |
| `--use-chrome` | 从 Chrome 浏览器获取 Cookie |
| `--page-size SIZE` | PDF 页面大小（A4, Letter, Legal），默认 A4 |
| `--landscape` | 使用横向页面 |
| `--set-default-dir DIR` | 设置默认输出目录 |

## 工作原理

1. **登录认证** - 使用 Playwright 启动浏览器，打开极客时间登录页面
2. **自动检测** - 轮询检测登录状态，用户完成登录后自动继续
3. **打开文章** - 在新标签页打开目标文章 URL
4. **页面处理** - 移除浮层、隐藏左侧导航栏
5. **滚动加载** - 滚动文章内容容器，加载所有动态内容
6. **生成 PDF** - 将完整内容导出为 PDF 文件

## 项目结构

```
geekbang-pdf/
├── main.py              # CLI 入口点
├── src/
│   ├── __init__.py      # 导出公共接口和异常类
│   ├── core/            # 核心模块
│   │   ├── __init__.py
│   │   ├── auth.py      # Selenium 登录 / Chrome 会话
│   │   ├── fetcher.py   # HTTP 页面获取
│   │   ├── parser.py    # HTML 解析（用于静态页面）
│   │   ├── converter.py # Playwright PDF 生成
│   │   └── exceptions.py # 自定义异常
│   ├── cli/             # CLI 模块
│   │   ├── __init__.py
│   │   ├── commands.py  # Click 命令定义
│   │   └── formatters.py # rich 输出格式化
│   ├── models/          # 数据模型
│   │   ├── __init__.py
│   │   ├── config.py    # PDFConfig dataclass
│   │   └── pdf_options.py # PDFOptions dataclass
│   └── utils/           # 工具模块
│       ├── __init__.py
│       ├── constants.py
│       ├── javascript.py
│       ├── logging_config.py
│       ├── selectors.py    # 平台选择器加载
│       └── waits.py
├── config/
│   ├── __init__.py
│   ├── config.py        # 配置文件管理（~/.geekbang-pdf/）
│   └── selectors.json   # 网站选择器配置
├── tests/
│   ├── unit/            # 单元测试
│   ├── integration/      # 集成测试
│   └── fixtures/        # 测试固件
├── docs/                # 文档目录
├── out/                 # PDF 输出目录
├── requirements.txt     # Python 依赖
└── package.json         # Node.js 依赖（Playwright）
```

## 配置文件

配置文件位于 `~/.geekbang-pdf/config.json`：

```json
{
  "cookie": "GCESS=xxx; GCID=yyy; ...",
  "default_output_dir": "/path/to/output"
}
```

## 常见问题

### Q: 提示 "没有保存的 Cookie"
A: 请使用 `--browser-login` 选项重新登录

### Q: PDF 内容被截断
A: 确保页面完全加载，工具会自动滚动加载所有内容

### Q: 页面是空白或只有部分内容
A: 极客时间页面是 SPA 应用，需要 JavaScript 渲染，请确保使用 `--browser-login` 模式

## 技术栈

- **Python 3.8+** - 主编程语言
- **Playwright** - 浏览器自动化
- **Selenium** - Chrome 会话连接（可选）
- **pypdf** - PDF 处理

## License

MIT License
