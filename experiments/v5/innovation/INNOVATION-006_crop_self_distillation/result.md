# V5-INNOVATION-006 结果

## 结论

两视角裁剪自蒸馏没有带来收益。seed 5 的 H 为 `74.1374`，比 local CE 对照低 `0.0348`，比完整模型均值低 `0.0909`；rescue `25`、harm `26`，纠错没有形成净收益，因此淘汰该方案。

## 结果

| RUN | seed | U | S | H | ZS | best epoch | global H | local H | rescue / harm |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RUN-001 | 5 | 72.3603 | 76.0041 | 74.1374 | 81.2801 | 31 | 74.0424 | 3.2254 | 25 / 26 |

运行 commit 为 `bd5cebd7604e3bb90a06f63777ec606fe16ffbab`。原始产物位于 `.runtime/runs/v5/local_evidence_rescue/V5-INNOVATION-006/RUN-001/`。本实验只有一个种子，只用于窄诊断。
