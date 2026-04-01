# CLAUDE.md

本项目为 Claude Code 提供代码工作指导。

## 项目概述

GeekBang PDF Saver - 用于将极客时间课程页面保存为 PDF 文件的 CLI 工具，支持完整的 JavaScript 渲染内容。

## 使用方式

```bash
# 推荐：自动弹出浏览器引导登录（首次使用）
python main.py <url> --browser-login

# 使用已保存的 Cookie
python main.py <url> --use-config

# 直接提供 Cookie
python main.py <url> --cookie "GCESS=xxx;..."

# 设置 PDF 页面大小
python main.py <url> --page-size Letter

# 输出到指定目录
python main.py <url> -o ./output
```

### 选项说明

| 选项 | 说明 |
|------|------|
| `--browser-login` | 推荐首次使用，自动弹出浏览器引导登录 |
| `--cookie` | 直接提供 Cookie 字符串 |
| `--use-config` | 使用配置文件中已保存的 Cookie |
| `--use-chrome` | 从 Chrome 浏览器获取 Cookie |
| `-o, --output` | 输出目录 |
| `-n, --name` | 输出文件名 |
| `--page-size` | PDF 页面大小（A4, Letter, Legal） |
| `--landscape` | 使用横向页面 |

## 项目结构

```
geekbang-pdf/
├── main.py              # CLI 入口点
├── src/
│   ├── __init__.py      # 导出公共接口和异常类
│   ├── auth.py          # Selenium 登录 / Chrome 会话
│   ├── fetcher.py       # HTTP 页面获取
│   ├── parser.py        # HTML 解析（用于静态页面）
│   ├── converter.py     # Playwright PDF 生成
│   └── exceptions.py    # 自定义异常
├── config/
│   └── config.py        # 配置文件管理（~/.geekbang-pdf/）
├── requirements.txt     # Python 依赖
└── package.json         # Node.js 依赖（Playwright）
```

## 核心实现细节

### 浏览器登录认证
- 使用 Playwright 的 `sync_playwright()` 启动无头浏览器
- 自动检测登录状态（轮询 URL 变化）
- 登录后在新标签页打开目标文章
- Cookie 自动保存到配置文件

### PDF 生成流程
1. 打开登录页面并等待用户登录
2. 登录成功后在新标签页打开目标 URL
3. 移除页面浮层（固定定位元素）
4. 隐藏左侧导航栏
5. 滚动加载完整文章内容（支持 SPA 动态加载）
6. 展开内容容器到完整高度
7. 生成 PDF（默认全屏高度）

### 关键技术点
- **Playwright**: 浏览器自动化，支持 SPA 内容渲染
- **自动登录检测**: 通过轮询 URL 判断登录状态
- **内容容器滚动**: 查找 `simplebar-content-wrapper` 等滚动容器
- **内容展开**: 将内部滚动容器展开为完整高度用于 PDF 生成
- **左侧导航隐藏**: 隐藏 `Index_side` 等侧边栏元素

### 重要提示
- 极客时间页面是 SPA - 内容需要 JavaScript 渲染
- 必须使用 `--browser-login` 选项完成登录
- PDF 生成使用 `full_page=True` 模式
- 文章内容容器使用 `simplebar` 滚动库，需要特殊处理

## 开发指南

### 安装依赖
```bash
pip install -r requirements.txt
npm install
```

### 运行测试
```bash
python main.py <url> --browser-login
```

### 代码规范
- 使用类型提示（type hints）
- 自定义异常继承自 `CustomError` 基类
- 配置文件存储在 `~/.geekbang-pdf/` 目录
