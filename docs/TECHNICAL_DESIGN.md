# GeekBang PDF Saver 技术设计文档

## 1. 系统架构设计

### 1.1 系统概述

GeekBang PDF Saver 是一个基于浏览器自动化的 CLI 工具，通过 Playwright 和 Selenium 实现极客时间课程页面的离线 PDF 保存。系统采用模块化设计，核心模块包括认证模块、转换模块、配置模块。

### 1.2 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py                                  │
│                      (CLI 入口点)                                │
└─────────────────────────────────────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│   auth.py       │  │  converter.py   │  │   config.py         │
│   (认证模块)     │  │  (转换模块)      │  │   (配置模块)        │
│                 │  │                 │  │                     │
│ - login()       │  │ - convert()     │  │ - load_config()     │
│ - login_with_   │  │ - convert_      │  │ - save_config()     │
│   cookie()      │  │   with_context()│  │ - get_cookie()      │
│ - get_cookies_  │  │                 │  │ - set_cookie()      │
│   from_chrome() │  │                 │  │                     │
└─────────────────┘  └─────────────────┘  └─────────────────────┘
         │                     │                     │
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│  exceptions.py  │  │  scripts/*.js   │  │ selectors.json      │
│  (异常体系)      │  │  (页面处理脚本) │  │ (网站选择器配置)     │
└─────────────────┘  └─────────────────┘  └─────────────────────┘
```

### 1.3 模块职责

| 模块 | 职责 | 依赖 |
|------|------|------|
| `main.py` | CLI 参数解析，流程编排 | argparse, all modules |
| `src/core/auth.py` | 浏览器登录认证，Chrome 会话管理 | Selenium, Playwright |
| `src/core/converter.py` | PDF 生成核心逻辑，页面处理 | Playwright |
| `src/core/fetcher.py` | HTTP 页面获取（备用） | requests |
| `src/core/parser.py` | HTML 解析，资源处理（备用） | BeautifulSoup |
| `src/core/exceptions.py` | 异常定义 | - |
| `config/config.py` | 配置文件读写，Cookie 加密存储 | cryptography |
| `src/models/` | 数据模型定义 | dataclasses |

### 1.4 数据流

```
用户输入 URL
      │
      ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  URL 验证   │────▶│  认证检查     │────▶│ 登录流程    │
└─────────────┘     └──────────────┘     └─────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  PDF 保存   │◀────│  PDF 生成    │◀────│ 页面处理    │
└─────────────┘     └──────────────┘     └─────────────┘
      │
      ▼
   完成
```

---

## 2. 模块设计

### 2.1 认证模块 (src/core/auth.py)

#### 设计目标
提供多种认证方式获取登录状态，支持手动登录和自动从 Chrome 获取 Cookie。

#### 核心接口

```python
def login(email: str, password: str, headless: bool = True, interactive: bool = False) -> str:
    """使用 Selenium 自动登录

    Args:
        email: 登录邮箱
        password: 登录密码
        headless: 是否隐藏浏览器
        interactive: 是否交互模式

    Returns:
        str: Cookie 字符串

    Raises:
        AuthError: 登录失败
    """

def login_with_cookie(cookie: str, headless: bool = True) -> bool:
    """验证 Cookie 是否有效

    Args:
        cookie: Cookie 字符串

    Returns:
        bool: Cookie 是否有效
    """

def get_chrome_user_data_dir() -> Optional[str]:
    """获取活跃的 Chrome 用户数据目录

    Returns:
        str or None: Chrome 用户数据目录路径
    """

def get_cookies_from_existing_chrome(debugging_port: int = 28800) -> Optional[str]:
    """从运行中的 Chrome 会话获取 Cookie

    Args:
        debugging_port: Chrome 调试端口

    Returns:
        str or None: Cookie 字符串
    """
```

#### 登录流程

```
1. 检测 Chrome 用户数据目录
   │
   ├─ 存在活跃 Chrome ──────▶ 连接已有会话
   │                              │
   │                              ▼
   │                         提取 Cookie
   │
   └─ 不存在或连接失败 ──────▶ 启动新会话
                                    │
                                    ▼
                              用户输入凭据
                                    │
                                    ▼
                               执行登录
                                    │
                                    ▼
                               保存 Cookie
```

### 2.2 转换模块 (src/core/converter.py)

#### 设计目标
处理页面内容滚动加载、浮层移除、导航隐藏等操作，最终生成 PDF。

#### 核心接口

```python
def convert_with_context(
    url: str,
    context: BrowserContext,
    output_path: Path,
    options: Optional[dict] = None
) -> None:
    """使用已有浏览器上下文转换 PDF

    Args:
        url: 目标 URL
        context: Playwright BrowserContext
        output_path: 输出文件路径
        options: PDF 选项
    """

def convert_with_cookie(
    url: str,
    cookie: str,
    output_path: Path,
    options: Optional[dict] = None
) -> None:
    """使用 Cookie 转换 PDF

    Args:
        url: 目标 URL
        cookie: Cookie 字符串
        output_path: 输出文件路径
        options: PDF 选项
    """

def convert_chrome_page_to_pdf(
    page: Page,
    output_path: Path,
    options: Optional[dict] = None
) -> None:
    """将已加载的 Chrome 页面转换为 PDF

    Args:
        page: Playwright Page 对象
        output_path: 输出文件路径
        options: PDF 选项
    """
```

#### PDF 生成步骤

1. **页面加载**
   - 设置 User-Agent 头
   - 等待页面加载（domcontentloaded）
   - 额外等待动态内容渲染（8秒）

2. **浮层移除** (`remove_floating_layers.js`)
   ```javascript
   // 移除固定/粘性定位的浮层
   // 包括：登录弹窗、推荐试读、订阅提示等
   ```

3. **内容区域处理** (`hide_sidebar.js`)
   ```javascript
   // 隐藏左侧边栏 (Index_side)
   // 隐藏右侧固定元素
   // 扩展主内容区域到全屏
   ```

4. **内容滚动加载** (`scroll_content.js`)
   ```javascript
   // 查找滚动容器 (simplebar-content-wrapper 等)
   // 渐进式滚动到底部
   // 触发懒加载内容
   ```

5. **内容展开** (`expand_content.js`)
   ```javascript
   // 将内部滚动容器展开为完整高度
   // 用于 PDF 生成时的全页捕获
   ```

6. **PDF 生成**
   ```python
   page.pdf(
       path=str(output_path),
       width=page_width,      # 根据 page_size 计算
       height=content_height,
       print_background=True,
       margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"}
   )
   ```

### 2.3 页面获取模块 (src/core/fetcher.py)

#### 设计目标
提供 HTTP 方式获取页面内容作为备用方案。

#### 核心接口

```python
def validate_url(url: str) -> bool:
    """验证 URL 是否为有效的极客时间 URL

    Args:
        url: 待验证的 URL

    Returns:
        bool: 是否有效
    """

def fetch_page(url: str, cookie: Optional[str] = None) -> tuple[str, str]:
    """获取页面 HTML

    Args:
        url: 目标 URL
        cookie: Cookie 字符串（可选）

    Returns:
        tuple: (html_content, title)
    """

def parse_cookie_string(cookie_str: str) -> dict:
    """将 'name=value; name=value' 解析为字典

    Args:
        cookie_str: Cookie 字符串

    Returns:
        dict: {name: value}
    """
```

### 2.4 HTML 解析模块 (src/core/parser.py)

#### 设计目标
处理 HTML 内容，转换相对路径，下载远程资源。

#### 核心接口

```python
def process_html(html: str, base_url: str) -> str:
    """处理 HTML 内容

    Args:
        html: 原始 HTML
        base_url: 基础 URL

    Returns:
        str: 处理后的 HTML
    """

def extract_article_content(html: str) -> str:
    """提取文章主体内容

    Args:
        html: HTML 字符串

    Returns:
        str: 文章内容 HTML
    """

def download_image(url: str, timeout: int = 10) -> Optional[str]:
    """下载图片到本地

    Args:
        url: 图片 URL
        timeout: 超时时间

    Returns:
        str or None: 本地相对路径
    """
```

---

## 3. API 设计

### 3.1 公共接口 (src/__init__.py)

```python
from src import (
    # Exceptions
    GeekBangError,
    URLInvalidError,
    FetchError,
    AuthError,
    ConversionError,
    ConfigError,
    # Auth
    login,
    login_with_cookie,
    get_cookies_from_existing_chrome,
    # Converter
    convert_with_context,
    convert_with_cookie,
    convert_chrome_page_to_pdf,
    # Fetcher
    fetch_page,
    validate_url,
    parse_cookie_string,
    # Parser
    process_html,
    extract_article_content,
)
```

### 3.2 核心模块接口 (src/core/__init__.py)

```python
from src.core import (
    # Exceptions
    GeekBangError,
    URLInvalidError,
    FetchError,
    AuthError,
    ConversionError,
    ConfigError,
    # Auth
    login,
    login_with_cookie,
    get_cookies_from_existing_chrome,
    # Converter
    convert_with_context,
    convert_with_cookie,
    convert_chrome_page_to_pdf,
    # Fetcher
    fetch_page,
    validate_url,
    parse_cookie_string,
    # Parser
    process_html,
    extract_article_content,
)
```

---

## 4. 数据模型设计

### 4.1 PDFConfig (src/models/config.py)

应用程序级配置数据类：

```python
@dataclass
class PDFConfig:
    """Configuration for the PDF saver application."""

    cookie: Optional[str] = None           # 会话 Cookie
    default_output_dir: Path = field(
        default_factory=lambda: Path.home() / ".geekbang-pdf"
    )                                      # 默认输出目录
    page_size: str = "A4"                 # 默认页面大小
    landscape: bool = False                # 默认横向模式
```

### 4.2 PDFOptions (src/models/pdf_options.py)

PDF 生成选项数据类：

```python
@dataclass
class PDFOptions:
    """Options for PDF generation."""

    page_size: str = "A4"                 # 页面大小 (A4, Letter, Legal)
    landscape: bool = False               # 是否横向
    wait_time: int = 5                    # 动态内容等待时间（秒）
    margin_top: str = "20mm"              # 上边距
    margin_bottom: str = "20mm"           # 下边距
    margin_left: str = "15mm"             # 左边距
    margin_right: str = "15mm"            # 右边距

    @classmethod
    def from_dict(cls, data: dict) -> "PDFOptions":
        """从字典创建 PDFOptions"""

    def to_dict(self) -> dict:
        """转换为字典"""
```

### 4.3 常量定义 (src/utils/constants.py)

```python
class ConversionConstants:
    """PDF 转换相关常量"""

    NAVIGATION_TIMEOUT_MS = 30000          # 导航超时（毫秒）
    LOGIN_TIMEOUT_EXTRA_MS = 60000        # 登录额外等待（毫秒）
    PAGE_LOAD_WAIT_MS = 8000              # 页面加载等待（毫秒）
    CONTENT_SCROLL_PAUSE_MS = 100         # 滚动暂停（毫秒）

class LoginConstants:
    """登录相关常量"""

    MAX_LOGIN_WAIT_SECONDS = 120          # 最大登录等待时间（秒）
    LOGIN_POLL_INTERVAL_SECONDS = 2       # 登录状态轮询间隔（秒）
    LOGIN_URL = "https://account.geekbang.org/login"

class PageConstants:
    """页面相关常量"""

    SUPPORTED_PAGE_SIZES = ["A4", "Letter", "Legal"]
    DEFAULT_PAGE_SIZE = "A4"
    VIEWPORT_WIDTH = 1920                 # 视口宽度（像素）
    MAX_CONTENT_HEIGHT = 4000             # 最大内容高度（像素）
```

---

## 5. 异常体系设计

### 5.1 异常层次

```
GeekBangError (基类)
├── URLInvalidError (URL)
├── FetchError (FETCH)
├── AuthError (AUTH)
│   ├── INVALID_CREDENTIALS (AUTH_001)
│   ├── SESSION_EXPIRED (AUTH_002)
│   └── LOGIN_TIMEOUT (AUTH_003)
├── ConversionError (CONV)
│   ├── NAVIGATION_FAILED (CONV_001)
│   └── CONTENT_LOAD_TIMEOUT (CONV_002)
└── ConfigError (CONFIG)
    ├── PATH_TRAVERSAL_BLOCKED (CONFIG_001)
    ├── COOKIE_ENCRYPTION_FAILED (CONFIG_002)
    └── COOKIE_DECRYPTION_FAILED (CONFIG_003)
```

### 5.2 异常基类实现

```python
class GeekBangError(Exception):
    """Base exception for GeekBang PDF Saver."""

    CODE = "UNKNOWN"
    DEFAULT_MESSAGE = "An unknown error occurred"

    def __init__(self, message: str = None, code: str = None):
        self.message = message or self.DEFAULT_MESSAGE
        self.code = code or self.CODE
        super().__init__(f"[{self.code}] {self.message}")
```

### 5.3 异常使用示例

```python
# 抛出异常
raise URLInvalidError("Invalid URL format")

# 捕获异常
try:
    convert_with_cookie(url, cookie, output_path)
except GeekBangError as e:
    print(f"Error [{e.code}]: {e.message}")
```

---

## 6. 配置管理设计

### 6.1 配置文件位置

- 路径: `~/.geekbang-pdf/config.json`
- 权限: 600 (仅所有者读写)

### 6.2 配置结构

```json
{
  "cookie": "encrypted_cookie_string",
  "default_output_dir": "/path/to/output",
  "page_size": "A4",
  "landscape": false
}
```

### 6.3 配置管理接口

```python
def load_config() -> dict:
    """加载配置文件

    Returns:
        dict: 配置对象
    """

def save_config(config: dict) -> None:
    """保存配置到文件

    Args:
        config: 配置对象
    """

def get_cookie() -> Optional[str]:
    """获取保存的 Cookie

    Returns:
        str or None: Cookie 字符串（解密后）
    """

def set_cookie(cookie: str) -> None:
    """保存 Cookie（加密存储）

    Args:
        cookie: Cookie 字符串
    """

def get_default_output_dir() -> Optional[str]:
    """获取默认输出目录"""

def set_default_output_dir(dir_path: str) -> None:
    """设置默认输出目录"""
```

### 6.4 Cookie 加密

使用 `cryptography.fernet.Fernet` 进行 Cookie 加密：

```python
from cryptography.fernet import Fernet

# 生成密钥（首次）
key = Fernet.generate_key()

# 加密
cipher = Fernet(key)
encrypted = cipher.encrypt(cookie.encode())

# 解密
decrypted = cipher.decrypt(encrypted).decode()
```

---

## 7. JavaScript 脚本设计

### 7.1 脚本清单

| 脚本 | 功能 | 关键选择器 |
|------|------|-----------|
| `remove_floating_layers.js` | 移除固定定位浮层 | `[style*="position: fixed"]`, `[style*="position: sticky"]` |
| `hide_sidebar.js` | 隐藏侧边栏 | `[class*="Index_side"]` |
| `find_content.js` | 定位内容区域 | `[class*="Index_contentWrap"]` |
| `scroll_content.js` | 滚动加载内容 | `.simplebar-content-wrapper` |
| `expand_content.js` | 展开内容高度 | 内容容器 |

### 7.2 浮层移除策略

```javascript
// 移除固定/粘性定位的浮层
document.querySelectorAll('*').forEach(el => {
    const style = window.getComputedStyle(el);
    if (style.position === 'fixed' || style.position === 'sticky') {
        const text = el.innerText || '';
        // 移除包含以下关键词的浮层
        if (text.includes('登录') ||
            text.includes('推荐试读') ||
            text.includes('订阅')) {
            el.remove();
        }
    }
});
```

### 7.3 内容滚动策略

```javascript
// 查找并滚动滚动容器
document.querySelectorAll('div').forEach(el => {
    const style = window.getComputedStyle(el);
    if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
        // 渐进式滚动
        while (el.scrollTop < el.scrollHeight) {
            el.scrollTop += window.innerHeight;
        }
    }
});
```

---

## 8. CLI 设计

### 8.1 命令行参数

```python
# 位置参数
url: str                  # 极客时间文章 URL（支持多个）

# 选项参数
--urls-file FILE          # 从文件读取额外 URL
-o, --output DIR          # PDF 输出目录
-n, --name NAME           # 输出文件名（单 URL 模式）
--cookie COOKIE           # 直接提供 Cookie
--use-config             # 使用配置文件中的 Cookie
--use-chrome             # 从 Chrome 获取 Cookie
--login                   # 手动登录并保存 Cookie
--browser-login           # 通过浏览器登录（推荐）
--page-size {A4,Letter,Legal}  # PDF 页面大小
--landscape              # 使用横向页面
--set-default-dir DIR    # 设置默认输出目录
```

### 8.2 命令执行流程

```
main()
  │
  ├─ args.login ──────────▶ handle_login()
  │                              │
  │                              ▼
  │                         登录并保存
  │
  ├─ args.set_default_dir ────▶ 设置默认目录
  │
  ├─ args.browser_login ──────▶ browser_login_and_save()
  │                              │
  │                              ├── login_and_get_context()
  │                              │     │
  │                              │     └── 浏览器登录
  │                              │
  │                              └── 批量转换 PDF
  │
  └─ 默认 ───────────────────▶ save_page()
       │                            │
       │                            ├── 获取 Cookie
       │                            │
       │                            └── 批量转换 PDF
```

---

## 9. 日志配置

### 9.1 日志级别

| 级别 | 使用场景 |
|------|----------|
| DEBUG | 详细调试信息 |
| INFO | 一般信息 |
| WARNING | 警告信息 |
| ERROR | 错误信息 |

### 9.2 日志格式

```python
%(asctime)s - %(name)s - %(levelname)s - %(message)s
# 示例: 2026-04-02 12:30:00 - geekbang_pdf - INFO - PDF saved successfully
```

---

## 10. 测试策略

### 10.1 测试目录结构

```
tests/
├── __init__.py
├── conftest.py           # pytest 配置
├── unit/                 # 单元测试
│   ├── test_config.py
│   └── test_exceptions.py
├── integration/          # 集成测试
└── fixtures/            # 测试固件
```

### 10.2 单元测试覆盖

| 模块 | 测试项 |
|------|--------|
| `config.py` | 配置加载/保存、Cookie 加解密 |
| `exceptions.py` | 异常创建、错误码验证 |

### 10.3 集成测试

- 完整的浏览器登录流程
- PDF 生成和保存
- 多 URL 批量处理

---

## 11. 安全设计

### 11.1 Cookie 保护

- 使用 Fernet 对称加密存储
- 文件权限 600
- 内存中解密使用后及时清理

### 11.2 路径安全

- 配置目录隔离在 `~/.geekbang-pdf/`
- 输出路径做相对路径检查
- 防止路径穿越攻击

### 11.3 输入验证

```python
def validate_url(url: str) -> bool:
    """验证 URL 必须是 geekbang.org 域名"""
    if not url.startswith("https://time.geekbang.org/"):
        raise URLInvalidError("URL must be from geekbang.org")
```

---

## 12. 性能优化

### 12.1 浏览器复用

- 多个 URL 共用同一浏览器上下文
- 避免重复启动浏览器

### 12.2 内容加载

- 滚动加载使用间歇性暂停
- 避免一次性滚动到底部导致内容截断

### 12.3 并发处理

- 当前版本串行处理多 URL
- 未来可考虑并发处理（需考虑登录状态共享）

---

*文档版本: 1.0.0*
*最后更新: 2026-04-02*
