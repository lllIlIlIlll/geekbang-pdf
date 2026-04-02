# GeekBang PDF Saver 产品需求文档

## 1. 产品概述

**项目名称：** GeekBang PDF Saver

**核心功能：** 命令行工具，将极客时间（geekbang.org）课程页面保存为 PDF 文件，支持完整的 JavaScript 渲染内容。

**解决的问题：** 用户希望将极客时间课程内容离线保存为 PDF，方便在没有网络或账号登录状态下阅读。

## 2. 功能需求

### 2.1 核心功能

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 浏览器登录 | 自动弹出浏览器引导用户登录，无需手动获取 Cookie | P0 |
| 自动登录检测 | 轮询检测登录状态，登录成功后自动继续 | P0 |
| PDF 生成 | 将课程页面保存为 PDF，支持完整内容 | P0 |
| Cookie 保存 | 登录成功后自动保存 Cookie 到配置文件 | P0 |
| 多标签页处理 | 登录页和文章页在不同标签页 | P1 |
| 内容滚动加载 | 自动滚动加载 SPA 动态渲染的完整内容 | P0 |
| 左侧导航隐藏 | 自动隐藏侧边栏，只保留文章内容 | P1 |
| 页面标题命名 | 使用页面标题作为 PDF 文件名 | P2 |
| 配置化平台支持 | CSS 选择器从 selectors.json 读取，支持多平台扩展 | P1 |

### 2.2 用户操作流程

```
1. 用户执行命令: python main.py <url> --browser-login
2. 工具自动打开浏览器到登录页面
3. 用户在浏览器中完成登录
4. 工具检测到登录成功，自动打开目标文章
5. 工具处理页面（移除浮层、隐藏导航）
6. 工具滚动加载完整内容
7. 生成 PDF 并保存到输出目录
```

### 2.3 多 URL 批量处理

工具支持一次性处理多个 URL，共享登录会话：

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 命令行多 URL | 通过空格分隔指定多个 URL | P0 |
| URL 文件加载 | 通过 `--urls-file` 从文件读取 URL | P1 |
| 共享会话 | 多 URL 共用同一浏览器上下文 | P0 |
| 进度追踪 | 显示当前处理进度和成功率 | P2 |

## 3. 技术实现

### 3.1 技术栈

- **Python 3.8+** - 主编程语言
- **Playwright** - 浏览器自动化，支持 SPA 内容渲染
- **Selenium** - Chrome 会话连接（可选）

### 3.2 关键实现

#### 自动登录检测
```python
# 轮询检测 URL 变化判断登录状态
while elapsed < max_wait_time:
    page.wait_for_timeout(poll_interval * 1000)
    login_status = page.evaluate(check_login_js)
    if not login_status['isOnLoginPage']:
        # 登录成功
        break
```

#### 内容滚动加载
```javascript
// 查找滚动容器
document.querySelectorAll('div').forEach(el => {
    const style = window.getComputedStyle(el);
    if (style.overflowY === 'auto' || style.overflowY === 'scroll') {
        // 滚动加载所有内容
    }
});
```

#### PDF 生成
```python
article_page.pdf(
    path=str(output_path),
    width="297mm",  # A3 宽度
    height=f"{content_height}px",
    print_background=True,
    margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"}
)
```

### 3.3 项目结构

```
geekbang-pdf/
├── main.py                 # CLI 入口点
├── src/
│   ├── __init__.py         # 导出公共接口和异常类
│   ├── core/               # 核心模块
│   │   ├── auth.py         # Selenium 登录 / Chrome 会话
│   │   ├── converter.py    # Playwright PDF 生成
│   │   ├── exceptions.py   # 自定义异常类
│   │   ├── fetcher.py      # HTTP 页面获取
│   │   └── parser.py       # HTML 解析（用于静态页面）
│   ├── cli/                # CLI 模块
│   │   ├── commands.py      # Click 命令定义
│   │   └── formatters.py   # rich 输出格式化
│   ├── models/             # 数据模型
│   │   ├── config.py       # PDFConfig dataclass
│   │   └── pdf_options.py  # PDFOptions dataclass
│   └── utils/              # 工具模块
│       ├── constants.py     # 常量定义
│       ├── javascript.py    # JavaScript 脚本管理
│       ├── logging_config.py # 日志配置
│       ├── selectors.py     # 平台选择器加载
│       └── waits.py         # 等待策略
├── config/
│   ├── config.py           # 配置文件管理（~/.geekbang-pdf/）
│   └── selectors.json      # 网站选择器配置
├── scripts/                 # JavaScript 脚本
│   ├── expand_content.js    # 内容区域展开
│   ├── find_content.js      # 内容区域定位
│   ├── hide_sidebar.js      # 侧边栏隐藏
│   ├── remove_floating_layers.js # 浮层移除
│   └── scroll_content.js    # 内容滚动加载
├── tests/                   # 测试目录
├── docs/                    # 文档目录
├── requirements.txt          # Python 依赖
├── requirements-dev.txt     # 开发依赖
├── pyproject.toml           # 项目配置
└── package.json            # Node.js 依赖
```

## 4. 命令行接口

### 4.1 选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `url` | 极客时间文章 URL | 必需 |
| `--browser-login` | 自动弹出浏览器引导登录 | 推荐 |
| `--cookie` | 直接提供 Cookie | - |
| `--use-config` | 使用已保存的 Cookie | - |
| `--use-chrome` | 从 Chrome 获取 Cookie | - |
| `-o, --output` | 输出目录 | ./output |
| `-n, --name` | 输出文件名 | 页面标题 |
| `--page-size` | PDF 页面大小 | A4 |
| `--landscape` | 使用横向 | false |

### 4.2 使用示例

```bash
# 推荐：自动浏览器登录
python main.py <url> --browser-login

# 使用已保存的 Cookie
python main.py <url> --use-config

# 指定输出目录和文件名
python main.py <url> -o ./output -n myfile --browser-login
```

## 5. 配置文件

路径：`~/.geekbang-pdf/config.json`

```json
{
  "cookie": "GCESS=xxx; GCID=yyy; ...",
  "default_output_dir": "/path/to/output"
}
```

## 6. 成功标准

- [ ] 给定有效 URL，能够成功生成 PDF 文件
- [ ] PDF 中包含完整的文章文字内容
- [ ] 左侧导航栏已被隐藏
- [ ] Cookie 自动保存，下次无需重复登录
- [ ] 错误提示信息清晰

## 7. 未来优化方向

- [x] 支持批量保存多个页面
- [x] 支持自定义 PDF 页面尺寸
- [x] 配置化平台支持框架（selectors.json）
- [ ] 支持保存代码块语法高亮
- [ ] 支持生成分章节的 PDF
- [ ] 支持更多平台（得到、知乎等）

## 8. 错误处理机制

### 8.1 异常体系

工具定义了完整的异常层次体系，便于错误定位和处理：

| 异常类 | 错误码 | 说明 |
|--------|--------|------|
| `GeekBangError` | UNKNOWN | 基类异常 |
| `URLInvalidError` | URL | URL 格式无效 |
| `FetchError` | FETCH | 页面获取失败 |
| `AuthError` | AUTH | 认证失败 |
| `ConversionError` | CONV | PDF 转换失败 |
| `ConfigError` | CONFIG | 配置操作失败 |

### 8.2 认证错误

| 错误类型 | 错误码 | 说明 |
|----------|--------|------|
| 无效凭据 | AUTH_001 | 用户名或密码错误 |
| 会话过期 | AUTH_002 | Cookie 已过期 |
| 登录超时 | AUTH_003 | 登录等待超时 |

### 8.3 转换错误

| 错误类型 | 错误码 | 说明 |
|----------|--------|------|
| 导航失败 | CONV_001 | 页面导航失败 |
| 内容加载超时 | CONV_002 | 动态内容加载超时 |

### 8.4 配置错误

| 错误类型 | 错误码 | 说明 |
|----------|--------|------|
| 路径穿越 | CONFIG_001 | 尝试访问配置文件范围外路径 |
| Cookie 加密失败 | CONFIG_002 | Cookie 加密失败 |
| Cookie 解密失败 | CONFIG_003 | Cookie 解密失败 |

## 9. 数据模型定义

### 9.1 PDFConfig

应用程序配置数据类：

```python
@dataclass
class PDFConfig:
    cookie: Optional[str] = None           # 会话 Cookie
    default_output_dir: Path = ...         # 默认输出目录
    page_size: str = "A4"                 # 默认页面大小
    landscape: bool = False                # 默认横向模式
```

### 9.2 PDFOptions

PDF 生成选项数据类：

```python
@dataclass
class PDFOptions:
    page_size: str = "A4"                 # 页面大小
    landscape: bool = False               # 是否横向
    wait_time: int = 5                    # 动态内容等待时间（秒）
    margin_top: str = "20mm"              # 上边距
    margin_bottom: str = "20mm"           # 下边距
    margin_left: str = "15mm"             # 左边距
    margin_right: str = "15mm"            # 右边距
```

## 10. 安全考虑

### 10.1 认证安全

- ✅ Cookie 存储在用户本地 `~/.geekbang-pdf/` 目录
- ✅ Cookie 存储采用 Fernet 对称加密（cryptography 库）
- ⚠️ 当前无 Cookie 过期机制，需手动刷新

### 10.2 输入验证

- ✅ URL 格式验证（必须是 geekbang.org 域名）
- ✅ 路径穿越防护（ConfigError.PATH_TRAVERSAL_BLOCKED）
- ⚠️ 建议定期更换 Cookie

### 10.3 安全建议

1. **Cookie 管理**
   - 定期使用 `--browser-login` 刷新会话
   - 不在命令行中直接传递敏感 Cookie

2. **文件系统**
   - 配置文件权限设置为 600（仅所有者读写）
   - 避免在共享目录存储配置文件

3. **网络传输**
   - 所有请求通过 HTTPS 进行
   - 不传输明文敏感信息

## 11. 非功能性需求

### 11.1 性能需求

| 指标 | 要求 |
|------|------|
| 单页 PDF 生成时间 | < 30 秒 |
| 多页批量处理 | 每页约 20-30 秒 |
| 内存占用峰值 | < 500MB |
| 浏览器启动时间 | < 5 秒 |

### 11.2 兼容性需求

| 项目 | 要求 |
|------|------|
| Python 版本 | 3.8+ |
| Node.js 版本 | 16+（推荐） |
| 操作系统 | macOS / Linux / Windows |
| 浏览器 | Chromium（通过 Playwright 安装） |

### 11.3 依赖版本

| 依赖 | 最低版本 |
|------|----------|
| requests | >=2.28.0 |
| beautifulsoup4 | >=4.11.0 |
| selenium | >=4.8.0 |
| lxml | >=4.9.0 |
| websocket-client | >=1.5.0 |
| cryptography | >=41.0.0 |

### 11.4 页面尺寸支持

| 尺寸 | 宽度 | 高度 |
|------|------|------|
| A4 | 210mm | 297mm |
| Letter | 8.5in | 11in |
| Legal | 8.5in | 14in |

### 11.5 可用性需求

- [ ] 错误信息本地化（中文）
- [ ] 命令行帮助信息完整
- [ ] 支持 Ctrl+C 中断
- [ ] 进度提示清晰
