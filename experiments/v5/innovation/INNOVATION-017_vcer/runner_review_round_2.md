# VCER Runner 审核：第 2 轮

```text
round: 2
reviewer_id: /root/vcer_runner_review2
reviewed_code_id:
  vcer.py: 143dc00f92383012bfe0c797391dbf6a6e170057f4e3484765e2f8893a7dc720
  train.py: 3cfed93b1dfd77e55523dd4715af74156b571bd516b47fad3730ab1077985a34
  config.yaml: 0127650b913487db8d677e197ceb1ad803e6c4f979ade9854f079f1fab9bfa67
  tests/test_v5_vcer.py: 7b1ba15f8c78be14292c5186e73cec873ef921b4960d4359a8a9f3728f787d1b
  tests/test_v5_vcer_runner.py: 66b6ab59dae03acd011c1df35c76cadef8563c9892f9190d5b01a2d7ed25032b
reviewed_extra_files:
  - tests/test_v5_vcer_runner.py 的 portability 修复
  - train.py::verify_class_order
files_reviewed:
  - experiments/v5/innovation/INNOVATION-017_vcer/train.py
  - experiments/v5/innovation/INNOVATION-017_vcer/config.yaml
  - tests/test_v5_vcer_runner.py
machine_test_ref: py_compile pass; unittest 17/17 pass; git diff --check pass
previous_round_ref: experiments/v5/innovation/INNOVATION-017_vcer/runner_review_round_1.md
unresolved_blockers: 0
decision: pass
```

## 结论

- 生产端 `verify_class_order` 未改：正式运行仍读取真实 `att_splits.mat`，要求 `[200,1]`，并将真实类名序列与冻结 SHA-256 比较。
- 新测试的临时 MATLAB cell/string 结构与生产提取路径一致，同时覆盖正确摘要放行和错误摘要硬拒绝。
- 原配置测试仍断言冻结 `class_order_sha256` 常量；移除的只是测试期对本地大数据路径的依赖。
- X2 原型、200 类 U/S/H、50 类 ZS、checkpoint-before-official 和四个 official control 的语义均未改变。

## 未覆盖范围

未跨多个 SciPy/操作系统版本重复 round-trip；尚未执行真实 4090 显存 smoke、训练或 official tensor 读取。真实数据身份由正式 Runner 的输入 SHA 与类序双 gate 验证。
