# V5-INNOVATION-017 结果

```text
status: completed_stop_no_gain
decision: stop_no_gain
evidence_label: official-test-guided development
formal_evidence: false
promotion_decision: rejected
```

## 结论

VCER 明确失败。固定 epoch 50 的主结果 `H=64.120270`，相对同次冻结 X2
`H=73.523304` 下降 `9.403034`。主要问题是 unseen transfer 崩塌：U 下降
`16.093612`，而 S 只下降 `0.871086`；ZS 同时下降 `15.459520`。

角色因果门也未成立。role-shuffle 的 `H=65.547610`，反而比正确角色对应高
`1.427339`；unique-swap 只比 VCER 低 `0.085910`。因此共享低秩空间没有学到
可迁移的正确角色结构，不保留 VCER，不调 gamma 或 loss 权重，也不与 ARTV 叠加。

## 完整结果

| 条件 | U | S | H | ZS |
|---|---:|---:|---:|---:|
| X2 | 73.395479 | 73.651576 | 73.523304 | 81.534684 |
| VCER | 57.301867 | 72.780490 | 64.120270 | 66.075164 |
| role-shuffle | 59.274268 | 73.306012 | 65.547610 | 67.852479 |
| unique-swap | 57.101303 | 72.883660 | 64.034360 | 65.908504 |

训练 CE 从 `0.757554` 降到 `0.340351`，但 unique 因果损失从 `0.099998`
到 `0.099979`，几乎停在固定 margin；这与“seen 拟合增强、角色因果结构未形成、
unseen 大幅下降”的结果一致。

## 身份与证据

- run commit：`c7bc8ee7fda3271242ffbfb43100848825b6a9a4`
- config SHA-256：`0127650b913487db8d677e197ceb1ad803e6c4f979ade9854f079f1fab9bfa67`
- Warehouse：`warehouse://runs/v5/local_trials/VCER-20260817/RUN-001`
- `training.log`：`3e1fc27543efb45d4dc1732f7fdd0258c1193445b5a6142abdfcf57cf28778fb`
- `metrics.json`：`c16e0b9323d8ed83964a3a15f276a7ca9c75a55eb6db36f76eb3e63f5d4f60e7`
- `model_best.pth`：`5af4e752bcfb64e72608f2fc6cb33d45f28ff2ec8661a6d0b1671eabf6a903d3`

服务器没有保存数值退出码，因此参数矩阵留空；完成状态来自完整 `metrics.json`、
50 个 epoch 日志、正常结束进程和无 traceback 记录，不补造 `exit_code=0`。
