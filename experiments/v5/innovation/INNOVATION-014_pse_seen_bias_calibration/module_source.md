# 模块来源

- 类型：单标量 seen-logit 校准。
- 目的：直接修正共享 PSE 的 `S=74.99、U=63.23` 偏置。
- 边界：不改 PSE、不加局部分支、不加训练参数；按 owner 授权直接使用 test 搜索。
- 证据限制：`not_confirmation_evidence: true`。
