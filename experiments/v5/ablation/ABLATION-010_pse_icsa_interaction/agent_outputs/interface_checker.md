role: interface_checker
subject_id: V5-ABLATION-010
decision: allow
files_reviewed:
- EXPERIMENT.yaml
- implementation.md
- config.yaml
checks:
- 任务只切换冻结模板中的 PSE 与 ICSA 组合；数据和评估口径保持不变。
uncovered_scope:
- 真实 forward、loss 和 CUDA 行为须由服务器小跑确认。
