# GeekBang PDF Saver

极客时间课程页面 PDF 保存工具 - 将极客时间课程页面保存为 PDF 文件，支持完整的 JavaScript 渲染内容。

## 功能特性

- **浏览器登录认证** - 自动弹出浏览器引导登录，无需手动获取 Cookie
- **完整内容保存** - 支持 SPA 单页应用，完整保存 JavaScript 动态渲染内容
- **自动滚动加载** - 自动滚动页面加载所有内容
- **隐藏界面元素** - 自动隐藏左侧导航栏、浮层等非内容元素
- **Cookie 自动保存** - 登录成功后自动保存 Cookie，下次无需重复登录
- **Cookie 失效自动登录** - 使用已保存 Cookie 时会自动检测有效性，无效则跳转登录
- **多页面格式支持** - 支持 A4、Letter、Legal 等多种页面尺寸
- **配置化平台支持** - CSS 选择器从 `selectors.json` 读取，支持多平台扩展

## 安装

```bash
# 克隆项目
git clone https://github.com/lllIlIlIlll/geekbang-pdf.git
cd geekbang-pdf

# 方式1：使用安装脚本（推荐）
./install.sh

# 方式2：手动安装
pip3 install -r requirements.txt
npm install
npx playwright install chromium
```

## 快速开始

```bash
# 运行（交互式输入 URL）
./run.sh

# 或直接指定 URL
./run.sh https://time.geekbang.org/column/article/954158

# 首次使用会自动跳转浏览器登录
```

### 启动脚本使用方式

```bash
./run.sh                 # 交互式输入 URL
./run.sh <url>          # 下载单篇文章
./run.sh --batch        # 批量下载（使用 urls_batch.txt）
./run.sh --login        # 浏览器登录
./run.sh -h             # 显示帮助
```

### Python CLI

```bash
# 推荐：首次使用，自动弹出浏览器引导登录
python3 main.py <url> --browser-login

# 使用已保存的 Cookie（Cookie 无效时自动跳转登录）
python3 main.py <url> --use-config

# 指定输出目录
python3 main.py <url> --use-config -o ./output
```

## 命令行选项

| 选项 | 说明 |
|------|------|
| `url` | 极客时间文章 URL（必需） |
| `-o, --output DIR` | PDF 输出目录 |
| `-n, --name NAME` | 输出文件名 |
| `--browser-login` | 自动弹出浏览器引导登录 |
| `--cookie COOKIE` | 直接提供 Cookie 字符串 |
| `--use-config` | 使用配置文件中已保存的 Cookie（无效时自动跳转登录）|
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
├── run.sh               # 交互式启动脚本
├── install.sh           # 安装脚本
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
│   ├── config.py        # 配置文件管理（项目目录下）
│   └── selectors.json   # 网站选择器配置
├── tests/
│   ├── unit/            # 单元测试
│   ├── integration/      # 集成测试
│   └── fixtures/        # 测试固件
├── docs/                # 文档目录
├── out/                 # PDF 输出目录
├── urls_batch.txt       # 批量下载 URL 列表
├── requirements.txt     # Python 依赖
└── package.json         # Node.js 依赖（Playwright）
```

## 配置文件

配置文件位于项目 `config/config.json`：

```json
{
  "cookie": "GCESS=xxx; GCID=yyy; ...",
  "default_output_dir": "/path/to/output"
}
```

## 常见问题

### Q: 提示 "没有保存的 Cookie"
A: 工具会自动跳转浏览器登录，引导您完成登录

### Q: PDF 内容被截断
A: 确保页面完全加载，工具会自动滚动加载所有内容

### Q: 页面是空白或只有部分内容
A: 极客时间页面是 SPA 应用，需要 JavaScript 渲染，请确保使用 `--browser-login` 模式

## 技术栈

- **Python 3.8+** - 主编程语言
- **Playwright** - 浏览器自动化
- **Selenium** - Chrome 会话连接（可选）

## License

MIT License
