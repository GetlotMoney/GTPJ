# ATTEMPT-013 Work Items

## 状态

planned。本文件是正式表格的待跑入口，不是运行缓存。

## 50 Jobs Matrix

| Work item | Candidate | dynamic_direction_mode | h | weight_s2v | anchor_lambda | seeds | jobs | status |
|---|---|---|---:|---:|---:|---|---:|---|
| WI-013-A | DR047 | sample | 48 | 0.535 | 0.002 | 6,7,8,9,10,11,12,13,14,15 | 10 | planned |
| WI-013-B | DR020 | sample | 48 | 0.525 | 0.003 | 6,7,8,9,10,11,12,13,14,15 | 10 | planned |
| WI-013-C | DR041 | sample | 48 | 0.515 | 0.002 | 6,7,8,9,10,11,12,13,14,15 | 10 | planned |
| WI-013-D | A011DR042 | sample | 48 | 0.515 | 0.004 | 6,7,8,9,10,11,12,13,14,15 | 10 | planned |
| WI-013-E | A011DR020 | sample | 48 | 0.555 | 0.0045 | 6,7,8,9,10,11,12,13,14,15 | 10 | planned |

## 证据边界

- `ATTEMPT-012` 的 6 个 completed jobs 不进入本轮 50 jobs 计数。
- 本轮尚未产生 `summary.csv`、`result.yaml` 训练指标或 checkpoint evidence。
- 若后续真实运行，Runner 必须把每个 job 的 seed、config、commit、artifact uri 和 H/U/S 指标写回。

