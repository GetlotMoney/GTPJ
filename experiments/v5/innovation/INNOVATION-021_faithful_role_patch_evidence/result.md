# V5-INNOVATION-021 结果

状态：`rejected / stop_no_gain`。

正式 `RUN-001` 使用提交 `7d9e37781558893dae3904765655ef536ed983a1`、seed 5。先在 100/50 类不重叠 pseudo-GZSL 上选出 `λ=0.5`，保存冻结选择状态后，official test 的五个预注册条件各评估一次；未训练 adapter、未使用 gamma，也未用 official test 选参。

| 条件 | U | S | H | ZS |
|---|---:|---:|---:|---:|
| 同次 Mean8 | 66.894132 | 66.392905 | 66.642576 | 81.534684 |
| FRPE all patches | 66.766822 | 67.184049 | 66.974786 | 81.540906 |
| 删除最高范数 patch | 66.766822 | 67.128497 | 66.947171 | 81.574249 |
| 删除确定性随机 patch | 66.766822 | 67.184049 | 66.974786 | 81.540906 |
| top-k only，不减空间均值 | 65.794915 | 66.008782 | 65.901675 | 80.867910 |

FRPE 相对 Mean8：`delta_U=-0.127310`、`delta_S=+0.791144`、`delta_H=+0.332210`、`delta_ZS=+0.006223`。U、S 的下降门没有触发，但 H 增益低于预先冻结的 `+0.50` 保留门，因此结论为拒绝，不换 seed、不扩强度网格。

机制诊断说明两点：删除最高范数 patch 仅让 H 再降 `0.027614`，随机删除逐值不变，未发现明显的单个高范数 token 捷径；去掉空间均值校正后 H 降到 `65.901675`，说明相对空间背景的校正比单纯 top-k 峰值更重要。但它仍不足以形成可保留的原创模块。

证据：`warehouse://runs/v5/innovation/V5-INNOVATION-021/RUN-001`。

## GALA hard-rival gate（本地 debug）

GALA 使用提交 `10009415740db14530d3c47b2320b7c7be5f4140`、seed 5，在 xlsa17 `trainval_loc` 内做固定分层 80/20 训练/验证，运行 8 轮冻结全局与 4 轮小学习率联合训练；固定日程结束后才评估 official test。

| 对象 | U | S | H | ZS |
|---|---:|---:|---:|---:|
| 原始 PSE + ICSA + topology checkpoint | 71.751755 | 76.527846 | 74.062882 | 81.272805 |
| 联合训练后 gate-off global | 71.886832 | 76.511639 | 74.127170 | 81.272805 |
| 联合训练后 gate-on final | 71.886832 | 76.511639 | 74.127170 | 80.127472 |

联合训练相对原 checkpoint 只增加 `0.064288 H`，低于 `+0.3` 门槛；gate-on 与 gate-off 的 U/S/H 完全相同，说明 gate 对 GZSL top-1 没有净贡献，同时令 ZS 下降 `1.145333`。结论为 `stop_gate_no_h_gain_and_zs_harm`，不继续搜索阈值、隐藏维度、角色组合或额外 loss。

该结果是单 seed `local_debug_not_formal_evidence`，不能用于 confirmation、promotion 或论文正式结论。产物：`D:/Backup/Documents/Myself/GTPJ/.runtime/runs/v5/gala/RUN-DEBUG-GALA-SEED5/`；`training.log`、`metrics.json`、checkpoint SHA-256 分别为 `d3d397acc89896bcaacdbf4f40fc41dd8d133154be499b68ac780d548cbe1c00`、`0310677f736dd3fd2fc3b1ada0c1b0743ad2ef4f9cc51607340f8685ea377e30`、`e9e67b8e098a90a5288a1b085b6d03d52f3b38376a073129a3c020d4a3818d51`。
