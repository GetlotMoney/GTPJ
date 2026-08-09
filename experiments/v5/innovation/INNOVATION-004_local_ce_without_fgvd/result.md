# V5-INNOVATION-004 结果

## 结论

局部 CE 没有改善结果。seed 5 的 H 为 `74.1723`，只比 FGVD-off 控制组高 `0.0097`，比完整模型均值低 `0.0560`；局部分支单独 H 还从 `3.4728` 降到 `3.1879`，因此淘汰该方案。

## 结果

| RUN | seed | U | S | H | ZS | best epoch | global H | local H | rescue / harm |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RUN-001 | 5 | 72.3884 | 76.0462 | 74.1723 | 81.6473 | 31 | 74.0225 | 3.1879 | 31 / 30 |

运行 commit 为 `bd5cebd7604e3bb90a06f63777ec606fe16ffbab`。原始产物位于 `.runtime/runs/v5/local_evidence_rescue/V5-INNOVATION-004/RUN-001/`。本实验只有一个种子，只用于窄诊断。
