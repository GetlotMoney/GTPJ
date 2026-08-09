# V5-ABLATION-006：辅助损失作用

```yaml
experiment_id: V5-ABLATION-006
status: pre_run_gated
campaign_id: CAMP-20260809-v5-ablation100
base_template_id: MODEL-V5-TEMPLATE-V1
code_ref: 2f5fa5e631ef82658d4bac587cdfd17f3534cb35
implementation_status: review_pending
review_tier: review-1
formal_runtime_backend: server_detached_role_only
```

## 要回答的问题

在 V5 主路径不变时，比较五项辅助损失整体关闭和其中关键损失单独关闭后的差异。每个候选按 (seed, repeat) = (5,1)、(5,2)、(17,1)、(17,2) 排列，共 16 个冻结任务。

| 候选 | 唯一改动 |
|---|---|
| CE-ONLY | `lambda_consist/topo_pearson/bmdd/mpp/neg` 全部设为 0 |
| BMDD-OFF | 只把 `lambda_bmdd` 设为 0 |
| CONSIST-OFF | 只把 `lambda_consist` 设为 0 |
| LOCAL-AUX-OFF | `consist/bmdd/mpp/neg` 设为 0，topology 保持 0.1 |

两种子双重复不是 confirmation，只能作为消融搜索和稳定性观察。目录内基础 `config.yaml` 与 V5 模板逐字相同；每个 RUN 只允许候选字段和 `random_seed` 变化，进程内设备始终为 `cuda:0`。模板提交写入 `code_ref`，本分支最终冻结 HEAD 由后续 campaign 记录为 `run_commit`。

当前没有训练、指标、receipt、日志、checkpoint 或结果文件；通过机器验证和 review-1 前保持 `review_pending / pre_run_gated`。
