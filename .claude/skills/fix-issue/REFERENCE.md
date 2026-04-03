# Fix Issue 详细参考

## 常见问题类型

### PDF 生成问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| PDF 空白 | Cookie 无效 | 重新登录 |
| 内容截断 | 滚动容器未完全展开 | 检查 expand_content.js |
| 样式丢失 | CSS 未正确加载 | 检查页面渲染 |

### 登录问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 登录失败 | Cookie 过期 | 删除配置重新登录 |
| 重定向循环 | 页面结构变化 | 更新 selectors.json |
| 超时 | 网络问题 | 检查连接 |

## 调试命令

```bash
# 查看详细日志
python3 main.py <url> --verbose

# 检查 Cookie 状态
cat config/cookie.json

# 测试 selectors
python3 -c "from config.selectors import get; print(get('article_title'))"
```

## 相关文件

- `src/core/auth.py` - 认证逻辑
- `src/core/converter.py` - PDF 生成
- `config/selectors.json` - 页面选择器
