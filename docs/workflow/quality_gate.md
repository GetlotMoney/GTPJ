# 质量门

普通实验的 `quality_check.md` 是证据完整性检查；baseline promotion 的
`quality_check.md` 是强制门。自动 promotion 的完整规则见 `docs/workflow/promotion.md`。

换句话说：

- tune、ablation、confirmation：`quality_check.md` 帮助记录证据是否完整。
- module trial、ablation 或 tuned configuration 提升为正式 `vX`：必须通过 promotion quality gate。

运行实验前：

1. 检查 Git status。
2. 确认临时分支从当前 `main` 切出，并记录正确的 `base_code_tag`。
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

## Promotion Quality Gate

任何实验想提升为正式 `vX`，必须先记录：

```text
promotion_decision: promote
promote_to: vX
```

随后自动执行 `docs/workflow/promotion.md` 的硬门。必须满足：

- [ ] 父版本明确：`parent_version`、`parent_tag`、`base_code_tag` 已记录。
- [ ] tag 明确：trial tag 指向 README 中记录的 `code_commit`。
- [ ] 指标明确：父版本 H、trial H、delta H、U/S/ZS、best epoch 已记录。
- [ ] 对照明确：同 seed 对照已记录；高风险改动已说明是否需要多 seed。
- [ ] 配置明确：trial config 和新版本 config 路径已记录。
- [ ] 日志明确：原始日志路径和 Git 内日志副本路径已记录。
- [ ] 口径不变：class order、seen/unseen split、logits shape、metric calculation 未改变。
- [ ] 接口不乱：input/output shape、loss、eval、checkpoint 变化已声明。
- [ ] 关闭等价：switch off 能回到 `parent_version` 行为。
- [ ] 账本完整：VERSION、VERSION_TREE、EXPERIMENT_REGISTRY、PROJECT_STATUS、PROJECT_STRUCTURE、README 已更新。
- [ ] 创意树同步：`idea_tree/idea_tree.json.current_version` 和必要的 `version_scores.vX` 已更新。
- [ ] baseline tag 准备打在最终 `main` commit 上。
- [ ] 最终决策：`promotion_decision: promote`，且硬门未发现 blocking issue。

只满足 `H` 提升，但上面任一关键项缺失时，不允许 promotion；应记录
`promotion_decision: blocked` 或 `promotion_decision: rejected`。

未来工作流可以使用的决策值：

```text
not_applicable
promote
blocked
rejected
```

风险等级：

- `TUNE-LITE`：只改 config 的 tuning。
- `STANDARD`：ablation、dataset transfer 或低风险 switch。
- `STRICT`：新模块代码、新 loss、forward path、data flow 或 evaluation 变化。

OpenClaw 和 Codex 未来应写出兼容的 `quality_check.md` 文件。
