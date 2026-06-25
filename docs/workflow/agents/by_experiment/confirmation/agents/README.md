# Confirmation Agents

重新复现用于验证已有 baseline 是否可信。

## 启用角色

```text
Coordinator
Runner
Log Analyst
Quality Checker
```

## 默认禁用角色

```text
Implementer
Interface Checker
Reviewer
Result Analyst
```

## 编排

```text
Coordinator -> Runner -> Log Analyst + Quality Checker -> Coordinator
```

## 关键规则

- 固定 `base_code_tag`。
- 固定 config、seed、命令、数据 split 和 cache 口径。
- 不改模型结构。
- Runner 串行运行。
- Runner 只写 Warehouse raw artifacts。
- Log Analyst 记录 U/S/H/ZS、best epoch、log artifact id、URI、hash 和失败阶段。
- Quality Checker 确认证据完整，并确认 dataset split、label mapping、class order、metric calculation 与 baseline 可比。
- 复现失败只记录证据和下一步建议，不直接改 baseline。
