# V5-INNOVATION-020 结果

状态：`rejected / stop_no_gain`。

正式 `RUN-001` 使用提交 `384f0d519b8c890afba6211e849272ce6cd2caec`、seed 5；在 100/50 类不重叠 pseudo-GZSL 上选择 `lambda=0.1`，冻结选择状态后 official test 每个预声明条件只评估一次，未使用 gamma。

| 条件 | U | S | H | ZS |
|---|---:|---:|---:|---:|
| 同次 Mean8 | 66.894132 | 66.392905 | 66.642576 | 81.534684 |
| RACE aligned | 66.967028 | 66.120547 | 66.541096 | 81.270540 |
| no-contrast control | 67.167586 | 66.679317 | 66.922561 | 81.775165 |
| wrong-role control | 66.998214 | 66.077381 | 66.534612 | 81.369954 |

RACE 相对 Mean8：`delta_U=+0.072896`、`delta_S=-0.272357`、`delta_H=-0.101480`、`delta_ZS=-0.264144`，未达到预先冻结的 `delta_H >= 0.50` 保留门，结论为拒绝，不换 seed、不扩强度网格。

两个机制反例也很明确：wrong-role 与 aligned 几乎相同，而 no-contrast 反而得到 H=66.922561。由此不能声称“同角色 rival 竞争”有效；no-contrast 只是固定 control 的观察值，未按其自身验证集重新选参，不能把它当成新的最佳配置。

证据：`warehouse://runs/v5/innovation/V5-INNOVATION-020/RUN-001`。
