# 质量门（未来参考）

当前 GitHub 治理阶段不强制执行本文件。本文件保留的是未来 workflow 接入时可以学习的
质量门思想：实验运行前先确认代码、配置、日志和结果口径不会混乱。

运行实验前：

1. 检查 Git status。
2. 确认分支从正确的 version tag 切出。
3. 确认 config 改动只作用于当前实验。
4. 确认模块改动由 off switch 控制。
5. 如果有模块代码改动，确认满足 `docs/workflow/code_interface_contract.md`。
6. 确认日志和结果路径已经准备好。

模块接口检查：

- baseline-off path 能回到选定 base version 的行为；
- input 和 output 的 tensor shape 已记录；
- 除非明确记录为接口变更，否则 logits shape 和 class order 不变；
- 新 loss 默认关闭，并由 config 权重控制；
- 除非 trial 明确就是 evaluation 实验，否则 evaluation 语义不变；
- 训练前已记录最低验证证据。

未来工作流可以使用的决策值：

```text
ACCEPTED
REJECTED
```

风险等级：

- `TUNE-LITE`：只改 config 的 tuning。
- `STANDARD`：ablation、dataset transfer 或低风险 switch。
- `STRICT`：新模块代码、新 loss、forward path、data flow 或 evaluation 变化。

OpenClaw 和 Codex 未来应写出兼容的 `quality_check.md` 文件。
