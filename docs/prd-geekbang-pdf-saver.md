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
├── main.py              # CLI 入口
├── src/
│   ├── __init__.py
│   ├── auth.py          # 登录认证
│   ├── converter.py     # PDF 转换
│   ├── exceptions.py    # 异常类
│   ├── fetcher.py       # 页面获取（备用）
│   └── parser.py        # HTML 解析（备用）
├── config/
│   └── config.py        # 配置管理
├── docs/                # 文档
├── requirements.txt
├── package.json
└── README.md
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

- [ ] 支持批量保存多个页面
- [ ] 支持自定义 PDF 页面尺寸
- [ ] 支持保存代码块语法高亮
- [ ] 支持生成分章节的 PDF
