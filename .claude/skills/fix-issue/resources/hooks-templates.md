# Hook 配置模板

Hook = 把"记得自查"变成"必须自查"。
配置文件：`.claude/settings.json`（项目根目录）

---

## Python / pytest

```json
{
  "hooks": {
    "PostToolUse": [{"matcher": "Edit|Write",
      "hooks": [{"type": "command",
        "command": "pytest tests/unit/ -x -q 2>&1 | tail -20"}]}],
    "Stop": [{"hooks": [{"type": "agent",
        "prompt": "运行 pytest tests/ -v 确认所有测试通过，未通过前不结束。",
        "timeout": 120}]}]
  }
}
```

---

## Node.js / TypeScript

```json
{
  "hooks": {
    "PostToolUse": [{"matcher": "Edit|Write",
      "hooks": [{"type": "command",
        "command": "npm test -- --passWithNoTests 2>&1 | tail -20"}]}],
    "Stop": [{"hooks": [{"type": "agent",
        "prompt": "运行 npm test 确认全部通过，未通过前不结束。",
        "timeout": 120}]}]
  }
}
```

> pnpm → `pnpm test`，bun → `bun test`

---

## Go

```json
{
  "hooks": {
    "PostToolUse": [{"matcher": "Edit|Write",
      "hooks": [{"type": "command",
        "command": "go test ./... 2>&1 | tail -20"}]}],
    "Stop": [{"hooks": [{"type": "agent",
        "prompt": "运行 go test ./... 和 go vet ./... 确认全部通过。",
        "timeout": 120}]}]
  }
}
```

---

## Rust

```json
{
  "hooks": {
    "PostToolUse": [{"matcher": "Edit|Write",
      "hooks": [{"type": "command",
        "command": "cargo test 2>&1 | tail -20"}]}],
    "Stop": [{"hooks": [{"type": "agent",
        "prompt": "运行 cargo test 和 cargo clippy 确认全部通过。",
        "timeout": 180}]}]
  }
}
```

---

## 无测试降级方案（类型检查 + 构建验证）

```json
{
  "hooks": {
    "PostToolUse": [{"matcher": "Edit|Write",
      "hooks": [{"type": "command",
        "command": "tsc --noEmit 2>&1 | tail -10"}]}],
    "Stop": [{"hooks": [{"type": "agent",
        "prompt": "运行 tsc --noEmit 和构建命令确认无错误。",
        "timeout": 60}]}]
  }
}
```

Python 降级：`mypy src/ --ignore-missing-imports 2>&1 | tail -10`

---

## PostToolUse vs Stop

| Hook | 触发时机 | 作用 |
|------|---------|------|
| `PostToolUse` | 每次 Edit/Write 后 | 即时反馈，快速发现新引入错误 |
| `Stop` | Claude 准备结束前 | 最终验收，整体通过才说 Done |

最小可用配置：只配 `Stop` 也比没有强。
