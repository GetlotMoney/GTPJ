# V5-INNOVATION-007 结果

## 结论

固定 top-5 有界重排三次都没有提高 GZSL H，应淘汰。它能救回一部分样本，但误伤更多，说明“全局不确定”不能直接当作“局部值得相信”。

## 结果

| 来源模型 | rerank RUN | 来源 H | rerank H | ΔH | ZS | changed / rescue / harm |
|---|---|---:|---:|---:|---:|---:|
| local CE | RUN-001 | 74.1723 | 74.1658 | -0.0064 | 81.7320 | 207 / 69 / 73 |
| confusion contrast | RUN-002 | 74.2657 | 74.1427 | -0.1230 | 81.9320 | 212 / 67 / 74 |
| crop distill | RUN-003 | 74.1374 | 73.8145 | -0.3229 | 81.2505 | 206 / 52 / 74 |

三个来源全部在 commit `bd5cebd7604e3bb90a06f63777ec606fe16ffbab` 上按预注册的 `k=5`、`residual_cap=0.25` 运行，没有根据测试 H 选择参数。原始产物位于 `.runtime/runs/v5/local_evidence_rescue/V5-INNOVATION-007/`。
