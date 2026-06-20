# Review Gate

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
- 除非明确 review，否则 logits shape 和 class order 不变；
- 新 loss 默认关闭，并由 config 权重控制；
- 除非 trial 明确就是 evaluation 实验，否则 evaluation 语义不变；
- 训练前已记录最低验证证据。

Review decision 只能是：

```text
ACCEPTED
REJECTED
```

风险等级：

- `TUNE-LITE`：只改 config 的 tuning。
- `STANDARD`：ablation、dataset transfer 或低风险 switch。
- `STRICT`：新模块代码、新 loss、forward path、data flow 或 evaluation 变化。

OpenClaw 和 Codex 必须写出兼容的 review 文件。
