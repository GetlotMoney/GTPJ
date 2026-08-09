# ATTEMPT-014 结果

## 结论

ATTEMPT-014 已完成服务器冻结复现实验。有效运行是 `RUN-20260708-0002-h76-restore100-exact-repeat-2gpu`；第一次 `RUN-20260708-0001...` 因服务器无法解析本地 commit/branch，在训练前失败，不作为方法证据。

本轮 100 个 planned jobs 中，80 个完成、20 个因同候选已达到各自 `restore_target_H` 而跳过、0 个失败。没有任何完成 job 达到 `H>=75`。

## 关键结果

| 项目 | 数值 |
|---|---:|
| completed | 80 |
| skipped | 20 |
| failed | 0 |
| H>=75 | 0 |
| restored candidates | 12 / 20 |

## Best Single

| Job | Candidate | H | U | S | Target | 配置 |
|---|---|---:|---:|---:|---:|---|
| DR-022 | A011B01DR017 | 74.99 | 73.33 | 76.73 | 74.89 | h48, w=0.500, anchor=0.003 |

## 75.00 来源候选

| Candidate | Source H | Best H | Mean H | Min H | Restored |
|---|---:|---:|---:|---:|---|
| A011B01DR042 | 75.00 | 74.81 | 74.690 | 74.64 | false |
| A011B04DR036 | 75.00 | 74.80 | 74.684 | 74.54 | false |

因此本轮不能说明 75.00 已还原，也不能触发 promotion。

## 后续调参热点

最值得继续调的是 `direction_sample + h48 + 小 anchor`：

| 中心 | 本轮证据 | 判断 |
|---|---|---|
| w=0.500, anchor=0.003 | best 74.99, mean 74.775 | 最接近 75 |
| w=0.550, anchor=0.003 | best 74.92, mean 74.774 | near miss，但未还原 target 74.96 |
| w=0.545, anchor=0.002 | best 74.88, mean 74.875 | 均值很稳 |
| w=0.535, anchor=0.0015~0.0025 | best 74.86/74.82 | 稳定窄区间 |

不建议继续重押 `w=0.515, anchor=0.004`、`w=0.555, anchor=0.0045`、`anchor>=0.005` 或 `w=0.575`，除非作为少量边界探针。

## 决策

`result_state: tune_promising`。本轮是后续调参依据，不是 confirmation、promotion 或 baseline-grade evidence。
