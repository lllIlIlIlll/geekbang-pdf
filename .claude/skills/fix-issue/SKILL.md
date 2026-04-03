---
name: fix-issue
description: >
  This skill helps diagnose and fix bugs, errors, regression issues and unexpected behaviors.
  Triggered when user mentions "修复", "fix", "bug", "报错", "error", "issue",
  "失败", "崩溃", "线上告警", "异常", "不工作", "挂了", "broken", "crash", "not working",
  or similar problem-related keywords.
  Always follow: reproduce → acceptance criteria → minimal fix → verify → update CLAUDE.md.
  NOT triggered by: general questions, feature requests, "how to" questions.
---

# Fix Issue Skill

> **核心约束：验收标准先于代码。修没修好，跑验证说了算，不是嘴说了算。**

---

## Checklist

每次修复严格按此顺序推进，用 TodoWrite 逐项跟踪：

- [ ] Phase 1: 复现 Bug，确认根因，列出待改文件
- [ ] Phase 2: 验收标准已获用户确认
- [ ] Phase 3: 最小化修复完成，输出变更摘要
- [ ] Phase 4: 所有验证项通过（附实际输出）
- [ ] Phase 5: CLAUDE.md 已更新

---

## 一键启动 Prompt

```
我遇到了一个 Bug，请严格按 Phase 1→5 顺序执行，不要跳步：

报错信息：{完整报错 / 堆栈跟踪}
复现命令：{最短可复现命令}
复现步骤：{1. 步骤一  2. 步骤二  3. 步骤三}
预期结果：{应该发生什么}
实际结果：{实际发生了什么}

Phase 1：先不要改代码 → 复现 Bug → 说明根因 → 列出计划改动的文件
Phase 2：建立验收标准 → 等我确认后再继续
Phase 3：最小化修复 → 输出变更摘要表
Phase 4：运行所有验证 → 输出每项 ✅/❌ → 失败最多重试 3 轮
Phase 5：更新 CLAUDE.md → 写入根因/修复/防范

在测试没有全部通过之前，不要告诉我"已经修好了"。
```

---

## Phase 1 · 复现 & 分诊

**先不要改代码。** 在理解问题之前动手，是一切返工的根源。

**所需信息（不全则先索取）：**

```
报错信息  → 完整报错文本 / 堆栈跟踪
复现命令  → 能稳定触发问题的最短命令
复现步骤  → 1. xxx  2. xxx  3. xxx
预期 vs 实际 → 本来应该发生什么 / 实际发生了什么
```

**信息到位后输出三件事：**
1. 确认可以复现（或说明无法复现的原因及替代方案）
2. 一句话说明最可能的**根因**（不是症状）
3. 列出准备修改的文件及理由

**快速分类（通用模式）：**

| 报错特征 | 类型 | 排查入口 |
|---------|------|---------|
| 认证失败 / Token 失效 / 登录循环 | 认证 | auth 模块 / session 管理 / token 刷新逻辑 |
| 网络超时 / 请求失败 / 429 / DNS 错误 | 网络 | HTTP 客户端 / 重试 / 限流策略 |
| 数据解析失败 / 空值 / 格式不匹配 | 数据处理 | 解析层 / 数据模型 / schema 验证 |
| 配置读取失败 / 环境变量缺失 / 路径错误 | 配置 | 配置加载器 / .env / 初始化顺序 |
| ImportError / ModuleNotFoundError / 依赖缺失 | 环境 | 依赖清单 / 虚拟环境 / 构建脚本 |
| UI 元素找不到 / 选择器失配 / 渲染异常 | 前端 | 选择器配置 / DOM 结构 / 版本兼容 |
| DB 连接失败 / 查询报错 / 迁移失败 | 存储 | 连接配置 / ORM 层 / 迁移脚本 |
| 并发冲突 / 竞态 / 死锁 / 结果不一致 | 并发 | 锁机制 / 事务 / 异步任务调度 |

> ⚡ **P0/P1 紧急**（服务宕机 / 数据丢失 / 安全漏洞）：跳过等待确认，立即修复，事后补 AC 文档。

各类 Bug 完整 AC 模板 → **[resources/ac-templates.md](resources/ac-templates.md)**

---

## Phase 2 · 验收标准（确认后才能动代码）

呈现以下内容，**等待用户确认，再写任何修复代码**：

```
### 📋 修复验收标准

Bug：[错误标识 + 一句话描述，如：[AUTH-002] Token 失效后请求未自动刷新]

❌ 必须消失
- [ ] [精确报错信息，原文抄录]
- [ ] [错误的用户可见现象]

✅ 必须出现
- [ ] [具体可观测的成功信号]
- [ ] [如可测试：必须通过的命令 / 必须返回的值]

🔬 验证方案
| 方式     | 命令                              |
|---------|----------------------------------|
| 单元测试  | {项目单元测试命令}                 |
| 集成测试  | {集成测试命令（若有）}             |
| 手动验证  | {最短可复现命令}                  |

🛡️ 回归防护
- 运行：{完整测试套件命令}
- 新增：{测试文件路径}::test_{用例名}（修复前必须失败）

---
*确认以上标准 / 调整后继续。*
```

---

## Phase 3 · 最小化修复

### 不可绕过的规则

| 规则 | 说明 |
|------|------|
| **最小变更** | 只改满足验收标准所需的最少代码 |
| **修根因不修症状** | 删掉修复后 Bug 若复现，说明只修了症状，须重新定位根因 |
| **禁止范围蔓延** | 发现邻近坏代码？开 Issue，此处不动 |
| **遵守项目规范** | 沿用项目已有的异常类 / 类型注解 / 编码风格 |
| **配置外置** | 可变值（选择器、阈值、路径）只改配置文件，禁止硬编码进业务逻辑 |
| **每处变更注明理由** | 改了什么 / 为什么改 / 改之前是什么 |

**修复完成后输出：**

```
### 🔧 变更摘要
| 文件 | 类型 | 说明 |
|------|------|------|
| [路径] | 修改/新增 | [一句话] |

根本原因：[一句话]
修复方式：[改了什么，为什么有效]
风险评估：低 / 中 / 高 — [理由]
```

---

## Phase 4 · 自动验证循环

```
运行 AC 中全部检查项
        │
   全部通过？
  ┌──Yes──┴──No──┐
  ▼               ▼
Phase 5       重新审视根因假设
              → 只修失败那一项
              → 最多自动重试 3 轮
              → 3 轮后停下汇报卡点，等待介入
```

**必须输出：** 每项的 ✅/❌ + 实际命令输出。
"应该好了" ≠ 验证通过。

---

## Phase 5 · 更新 CLAUDE.md（每次必须执行）

**每次修复后必须将教训写入 CLAUDE.md**，防止团队反复踩坑。

在文件末尾追加：

```markdown
### [YYYY-MM-DD] {问题简述，10字以内}
- **现象：** {用户看到的症状}
- **根因：** {技术原因，一句话}
- **修复：** {改了什么，为什么有效}
- **防范：** {以后如何避免——必须可执行，不能泛泛而谈}
- **相关文件：** {文件路径列表}
- **回归测试：** {测试文件路径}::{测试用例名}
```

CLAUDE.md 写作规范 → **[resources/claude-md-guide.md](resources/claude-md-guide.md)**

---

## 诊断工具

项目提供诊断和验证脚本，位于 `.claude/skills/fix-issue/scripts/` 目录，从项目根目录运行。

> **前置依赖**：PDF 验证需要 `pdfinfo`（macOS: `brew install poppler`，Linux: `apt install poppler-utils`）

```bash
# 诊断
python3 .claude/skills/fix-issue/scripts/helper.py pdf_blank
python3 .claude/skills/fix-issue/scripts/helper.py login_failed

# 验证修复
python3 .claude/skills/fix-issue/scripts/validator.py cookie
python3 .claude/skills/fix-issue/scripts/validator.py pdf out/test.pdf
python3 .claude/skills/fix-issue/scripts/validator.py selector article_title
```

完整诊断命令、常见问题速查、文件索引 → **[REFERENCE.md](REFERENCE.md)**

---

## Hook 自动化（推荐配置）

在 `.claude/settings.json` 中配置，让 Claude 每次改完文件自动跑测试：

```json
{
  "hooks": {
    "PostToolUse": [{"matcher": "Edit|Write",
      "hooks": [{"type": "command",
        "command": "{YOUR_TEST_CMD} 2>&1 | tail -20"}]}],
    "Stop": [{"hooks": [{"type": "agent",
        "prompt": "运行完整测试套件确认全部通过，未通过前不结束。",
        "timeout": 120}]}]
  }
}
```

各技术栈（Python / Node / Go / 无测试降级）模板 → **[resources/hooks-templates.md](resources/hooks-templates.md)**

---

## 反模式速查

| ❌ 禁止 | ✅ 应该 |
|--------|--------|
| `catch(e){}` 吞异常 / 调用处加空值判断掩盖问题 | 消除导致问题的根本条件 |
| 说"已修好"但不运行检查 | 运行所有检查，粘贴实际输出 |
| 修 Bug 时顺手重构/清理 | 先修 Bug，改进另开 PR |
| 可变配置（选择器、阈值）硬编码进业务代码 | 外置到配置文件，通过接口读取 |
| 抛出不符合项目规范的裸异常 | 使用项目已有的异常类层次和 error code |
| 修完不写 CLAUDE.md | 每次必须沉淀经验 |
| 无限次自动重试 | 最多 3 轮，停下汇报卡点 |

完整反模式与排查技巧 → **[resources/anti-patterns.md](resources/anti-patterns.md)**

---

## 典型使用示例

### 快速示例：有明确报错的修复

**用户**："PDF 生成出来是空白的，报错 `Cookie invalid: session expired`"

**Phase 1 输出**：
> 已复现：使用过期 Cookie 运行 `python3 main.py <url> --use-config` 得到空白 PDF。
> 根因：`src/core/auth.py` 中 Cookie 过期后未触发刷新/重登录流程，直接使用失效凭证请求页面。
> 计划修改：`src/core/auth.py`（增加过期检测）、`config/config.py`（清除无效凭证）

**Phase 2** → 呈现 AC → 等待确认 → **Phase 3-5** 按流程执行。

更多场景（间歇性 Bug、无报错但结果异常、示例选择指南）→ **[EXAMPLES.md](EXAMPLES.md)**
