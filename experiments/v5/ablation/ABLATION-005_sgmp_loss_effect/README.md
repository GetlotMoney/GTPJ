# V5-ABLATION-005：SGMP 损失项作用

```yaml
experiment_id: V5-ABLATION-005
status: pre_run_gated
campaign_id: CAMP-20260809-v5-ablation100
base_template_id: MODEL-V5-TEMPLATE-V1
code_ref: 2f5fa5e631ef82658d4bac587cdfd17f3534cb35
implementation_status: review_pending
review_tier: review-1
formal_runtime_backend: server_detached_role_only
```

## 要回答的问题

在 V5 其他配置完全不变时，分别把 SGMP 的 MPP 系数、NEG 系数或二者同时设为 0，观察各损失系数对结果的贡献。每个候选按 (seed, repeat) = (5,1)、(5,2)、(17,1)、(17,2) 排列，共 12 个冻结任务。

| 候选 | 唯一改动 | 不变项 |
|---|---|---|
| MPP-OFF | `lambda_mpp=0` | `lambda_neg=0.01` |
| NEG-OFF | `lambda_neg=0` | `lambda_mpp=0.05` |
| SGMP-ALL-OFF | 两个系数都为 0 | 其余 V5 配置不变 |

## 解释边界

MPP-OFF 只是系数消融，不是移除 SGMP；NEG 仍使用 pos_sim.detach。两种子双重复不是 confirmation，只能作为消融搜索和稳定性观察，不能写成复现或正式确认。

目录内 `config.yaml` 与 `experiments/v5/config.yaml` 逐字相同；每个 RUN 的快照只允许候选字段和 `random_seed` 相对模板变化，进程内设备始终为 `cuda:0`。模板提交是参数表的 `code_ref`；本分支最终 pre-run freeze HEAD 才由后续 campaign 记录为 `run_commit`，这里不提前伪造自指提交。

当前没有训练、指标、receipt、日志、checkpoint 或结果文件。通过机器验证和 review-1 前保持 `review_pending / pre_run_gated`。
