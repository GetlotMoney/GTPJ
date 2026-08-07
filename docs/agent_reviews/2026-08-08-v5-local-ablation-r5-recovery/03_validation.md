# 机器验证

- 本机控制器测试：51 项全部通过。
- 本机工作流测试：254 项全部通过。
- 本机 V5 消融与母版合同测试：14 项全部通过，1 项 CUDA 专属用例按平台跳过。
- 服务器准确候选 `58fa5a8`：控制器、真实 Linux 和中文解析共 57 项全部通过。
- 服务器 CUDA：7 项全部通过；FULL 与 GLOBAL_ONLY 均真实使用 CUDA 初始化。
- 服务器 V5 数学、复现、母版合同和消融语义：32 项全部通过。
- 服务器直接读取正式 16 行参数表并执行完成历史清单校验，返回的冻结任务准确为 `RUN-013…016`。
- `RUN-007` 清单 SHA-256 为 `3eb27b0e18327ebcef8d89131040322851302deedbdd6a594b8bf58973c4146b`；`RUN-010` 为 `f7d6228fda5bd9ce99c191911022206697d88ece5d89dc0d558a300deecdf4ef`。
- 两张清单列出的 10 个服务器真实文件逐项重新计算 SHA-256 和大小，全部一致。
- 审核 bundle SHA-256 为 `b2c718e051827fe9c6a6fd7b0efe0db4c0dbb0da8ba80f610c42f1d4d7347965`，共 14 项引用，HEAD 与实验分支均指向 `58fa5a8`。
- `py_compile`、`git diff --check`、参数表 selected-ready 校验和 `validate-experiment-base` 全部通过。

服务器测试日志位于 `.runtime/reviews/58fa5a8-linux-57.log`、`58fa5a8-cuda-7.log` 和 `58fa5a8-v5-32.log`。
