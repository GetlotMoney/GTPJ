# 执行卡：升版 Promotion

当某个结果可能成为新 baseline/version 时使用。

## 必读

```text
START_HERE.md
WORKFLOW_KERNEL.md
docs/workflow/protocols/promotion.md
docs/workflow/protocols/quality_gate.md
docs/workflow/protocols/versioning.md
docs/workflow/protocols/git_policy.md
```

## 角色

promotion 必须做正式独立检查：

```text
总控 (Coordinator)
证据质量检查 (Evidence Quality Checker)
接口检查 (Interface Checker)
结果比较 (Result Comparator)
复核者 (Reviewer)
```

promotion、baseline-grade、新版本、tag 和争议结果复核必须使用真实 `real_multi_agent`。
如果不能证明各角色有独立 agent 实例、独立输入和独立输出，promotion 必须阻断；
不能用 sequential review 或单窗口自查替代。

## 必要证据

```text
promotion_decision: promote
完整 manifest/result/quality/interface evidence
必要时有 repeat 或 confirmation evidence
已声明目标版本
没有未解决硬门
```

## 边界

只调参数不能创建新的 `vX`。

promotion 可以在协议要求时创建本地文件、commit 和 tag。

除非 owner 明确要求，否则不能 push。
