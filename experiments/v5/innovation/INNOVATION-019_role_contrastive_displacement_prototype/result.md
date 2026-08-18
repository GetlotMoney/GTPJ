# V5-INNOVATION-019 结果

状态：`rejected / stop_no_gain`。

正式 `RUN-001` 使用提交 `a86d76a00dd2ec8f8c4bdba197e823ec77375e0d`、seed 5 和 100/50 类不重叠验证选择 epoch 2；checkpoint 冻结后 official test 只评估一次，未使用 gamma。

| 模型 | U | S | H | ZS |
|---|---:|---:|---:|---:|
| 同次 Mean8 | 66.894132 | 66.392905 | 66.642576 | 81.534684 |
| RCDP | 64.528239 | 68.248612 | 66.336303 | 82.041609 |
| RCDP - Mean8 | -2.365893 | +1.855707 | -0.306272 | +0.506926 |

RCDP 提高了 S 和 ZS，但损失更多 U，H 下降 0.306272，未达到预先冻结的 `delta_H >= 0.50` 保留门。结论是拒绝该模块，不在它上面叠加 RPV、gamma 或其他模块。

证据：`warehouse://runs/v5/innovation/V5-INNOVATION-019/RUN-001`。
