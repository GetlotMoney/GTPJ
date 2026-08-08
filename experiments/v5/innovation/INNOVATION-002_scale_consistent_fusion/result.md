# V5-INNOVATION-002 结果

状态：`completed_stage1_gate_failed`

## 短结论

六个第一阶段任务均正常完成，legacy 复现正常；固定 `beta=0.05` 的尺度一致融合三次都使 H 下降，平均 `ΔH=-3.028825`。候选被否决，`RUN-007` 至 `RUN-010` 按预注册规则没有启动。

## 逐轮结果

| RUN | 路线 | seed | U | S | H | ZS | best epoch | 状态 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| RUN-001 | legacy | 5 | 72.195756 | 76.201117 | 74.144383 | 81.243533 | 36 | completed |
| RUN-002 | scale-consistent | 5 | 64.621490 | 78.661120 | 70.953464 | 81.110519 | 24 | completed |
| RUN-003 | legacy | 5 | 72.266847 | 76.244104 | 74.202218 | 81.314623 | 36 | completed |
| RUN-004 | scale-consistent | 5 | 65.693784 | 77.915698 | 71.284667 | 81.219029 | 25 | completed |
| RUN-005 | legacy | 5 | 72.670221 | 75.468636 | 74.042997 | 81.252342 | 31 | completed |
| RUN-006 | scale-consistent | 5 | 65.514028 | 77.643692 | 71.064991 | 80.303413 | 23 | completed |
| RUN-007 | legacy | 17 | — | — | — | — | — | stage1_gate_failed_not_started |
| RUN-008 | scale-consistent | 17 | — | — | — | — | — | stage1_gate_failed_not_started |
| RUN-009 | legacy | 29 | — | — | — | — | — | stage1_gate_failed_not_started |
| RUN-010 | scale-consistent | 29 | — | — | — | — | — | stage1_gate_failed_not_started |

## 三次均值

| 路线 | mean U | mean S | mean H | mean ZS |
|---|---:|---:|---:|---:|
| legacy | 72.377608 | 75.971286 | 74.129866 | 81.270166 |
| scale-consistent | 65.276434 | 78.073504 | 71.101041 | 80.877654 |
| scale − legacy | -7.101174 | +2.102218 | **-3.028825** | -0.392512 |

三组配对 H 差值：

- `RUN-002 − RUN-001 = -3.190918`
- `RUN-004 − RUN-003 = -2.917551`
- `RUN-006 − RUN-005 = -2.978006`

legacy 的 H 范围为 `[74.042997, 74.202218]`，极差仅 `0.159221`；scale-consistent 的 H 范围为 `[70.953464, 71.284667]`。

## 第一阶段门槛

| 门槛 | 结果 | 证据 |
|---|---|---|
| 六轮正常完成且证据齐全 | PASS | 六轮均 `completed`，数值有限，六类必需文件齐全 |
| legacy 平均 H 在 `74.17 ± 0.30` | PASS | `74.129866` 在 `[73.87, 74.47]` 内 |
| 三组 `ΔH > 0` | **FAIL** | 三组均为负 |
| 平均 `ΔH ≥ +0.50` | **FAIL** | 实际 `-3.028825` |
| `min(scale H) > max(legacy H)` | **FAIL** | `70.953464 < 74.202218` |
| 平均 U、S 均未下降超过 `0.30` | **FAIL** | U 下降 `7.101174`；S 提升 `2.102218` |

## 解释边界

结果支持一个窄而明确的判断：在当前 V5、固定 `beta=0.05` 和既定评估口径下，直接用共同 `logit_scale` 放大局部分数，会提高 S、显著损伤 U，因而不适合作为论文主线。

这不能推出“局部分支没有信息”。它只推翻“局部分支影响小主要是因为最后一步没有乘同一温度尺度”这一具体实现。看完结果后继续在 test 上搜索 beta 会造成调参泄漏，因此本实验不做系数续扫。

## 最终判断

`reject_scale_consistent_beta_0_05`。不启动第二阶段，不进入 confirmation 或 promotion；`not_confirmation_evidence: true`。失败代码、配置、日志和 checkpoint 全部保留。
