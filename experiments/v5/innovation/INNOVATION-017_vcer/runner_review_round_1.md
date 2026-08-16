# VCER Runner 审核：第 1 轮

```text
round: 1
reviewer_id: /root/vcer_runner_review1
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
  - experiments/v5/innovation/INNOVATION-017_vcer/vcer.py
  - experiments/v5/innovation/INNOVATION-017_vcer/train.py
  - experiments/v5/innovation/INNOVATION-017_vcer/config.yaml
  - tests/test_v5_vcer.py
  - tests/test_v5_vcer_runner.py
machine_test_ref: py_compile pass; unittest 17/17 pass; git diff --check pass
unresolved_blockers: 0
decision: pass
```

## 审核闭环

- 初审发现配置缺少 `class_order_sha256`，正式入口会在训练前报错；现已补入冻结值。
- X2 重建逐元素核对 checkpoint 的 sentence/adapted-class buffers，并保持历史 Value/Output、LayerNorm 与 `base_part + role_part.sum` 运算顺序。
- loss、梯度和更新后参数均有 NaN/Inf 硬停止；全局标签到 seen-local target 的映射已核对。
- 测试改为临时构造同形 `[200,1]` MATLAB 类名矩阵，不再依赖 clean worktree 内是否复制数据；正确 SHA 放行、错误 SHA 拒绝均已覆盖。
- 生产入口仍读取真实 `att_splits.mat` 并验证冻结类序 SHA，没有弱化运行时 hard gate。

## 未覆盖范围

尚未执行真实 4090 显存/吞吐 smoke，未加载 official tensor，未启动训练。
