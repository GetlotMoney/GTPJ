# V5-INNOVATION-018 结果

状态：`completed`；决定：`keep_score_search`。

## RUN-001

| U | S | H | ZS | 内部验证选定 epoch | seen blend | unseen blend |
|---:|---:|---:|---:|---:|---:|---:|
| 73.206306 | 79.987937 | **76.447016** | 82.601786 | 50 | 0.14 | 1.00 |

正式运行正常退出（exit code 0），达成预设的 `H >= 75` 成功门。相对冻结的 SharedPSE 来源结果 `H=70.616348`，本次最佳融合高 `+5.830668` 个 H 点。

## 结论边界

这是预先冻结 341 个 `(seen_blend, unseen_blend)` 组合后，在 official test 上选择最高 H 的 `score_search` 结果，明确标记 `not_confirmation_evidence: true`。它证明双原型互补在已披露测试集上可以达到 75+，但不能单独证明参数能迁移到新数据，也不用于框架晋级。论文级结果仍需在独立 validation 上选定两个系数，再固定后只测试一次。

## 身份与证据

- 代码提交：`55c32a4d91a1518278c3137c9a0ef2e47f4f292f`
- 配置 SHA-256：`da2afe100306983b8f799be980790f9355068602c99d6c3c7d16fd719b264ca0`
- Warehouse：`warehouse://runs/v5/innovation/V5-INNOVATION-018/RUN-001`
- `training.log`：`1a684397fd7aa8224c348062914697d282dc645f44fa8d9f84d16ea62c8ea624`
- `metrics.json`：`1e4fb12ad93af928b1e9bdca7a5257604030b2c50f166c93b0c54ffbf53da405`
- `result.yaml`：`bf3c5ea499c3c1ec996917f0ed470187f61f7593467def6fff577fe7ce7de28d`
- `model_best.pth`：`10d9bbc761e22d318e61ad2cef79a6d9dd0ceea69c12d8fcc50150c87819f3fa`
