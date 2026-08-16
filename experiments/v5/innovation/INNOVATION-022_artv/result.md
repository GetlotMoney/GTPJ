# V5-INNOVATION-022 结果

```text
status: completed_stop_no_gain
decision: stop_no_gain
evidence_label: official-test-guided-development
formal_evidence: false
promotion_decision: rejected
```

## 结论

ARTV 没有提高冻结 PSE-X2。主结果 `H=70.052722`，相对同次 X2
`H=73.523304` 下降 `3.470582`；U、S、ZS 也全部下降，因此不保留该模块，
不搜索 5/7 证书阈值、不加 gamma、不叠加后续模块。

角色干预存在但不足以挽救主路径：role-shuffle 比 ARTV 再低 `0.311694 H`，
unique-swap 比 ARTV 再低 `0.187567 H`。这说明投票并非完全忽略角色，但固定证书
错误交换过多。seen 上 harmed/rescued 为 `152/92`，unseen 为 `274/154`，两边均净伤害。

## 完整结果

| 条件 | U | S | H | ZS |
|---|---:|---:|---:|---:|
| X2 | 73.395479 | 73.651576 | 73.523304 | 81.534684 |
| ARTV | 69.360870 | 70.758516 | 70.052722 | 77.145910 |
| role-shuffle | 69.154203 | 70.337898 | 69.741028 | 77.040380 |
| unique-swap | 69.382185 | 70.354897 | 69.865155 | 77.537256 |

## 身份与证据

- run commit：`86fff007d134b3d6aa634f16b919c449f2d2931c`
- config SHA-256：`e86cbc635cfec1d39c82d82176cb626dfbc17fb6b9c8881d13456f13351dcac4`
- Warehouse：`warehouse://runs/v5/local_trials/ARTV-20260817/RUN-001`
- `evaluation.log`：`b2d2f898d0a19536884eea61a3066fec826980057fa00475f21f399fbfd33e4c`
- `metrics.json`：`590a4a7a064c27472519e67e30570eafc5c6c26cb5d04584da8784ada3f1145f`
- `artv_state.pth`：`bf1b6ad31d11e600b854fa9969ed1b6b8531fe92a0ff19b76ed65259824e87f7`
- seen/unseen crop：`2c0c9cfdcc864b01017cfbf98b2be12406bfe690a5b6e984072700c19b5be932` / `a63a92d36287d56c5865dc5d4d59c53940adde7184bc89c3e02b2ef94c22e342`

启动器没有持久化数值退出码，所以该字段留空；完成状态来自完整 `metrics.json`、
正常结束的进程和无 traceback 日志，不补造 `exit_code=0`。
