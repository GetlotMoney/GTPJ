# 参数矩阵：INNOVATION-017_vcer

| 任务 | 名称 | 状态 | 唯一改动 | seed | rank | batch | epochs | loss | 评估 | H | 决定 |
|---|---|---|---|---:|---:|---:|---:|---|---|---:|---|
| RUN-001 | VCER-on-X2-formal | frozen_ready | 冻结 X2 后只训练共享 VCER 低秩投影 | 5 | 16 | 8 | 50 | CE + unique causal + 0.05 preserve | 直接 official，固定 epoch 后读取 |  | pending |

Owner 于 2026-08-16 明确取消 pseudo-GZSL 前置门。该结果必须标记为
`official-test-guided development`，不作为未见测试或 confirmation 证据。
