role: interface_checker
subject_id: V5-ABLATION-008
decision: allow
files_reviewed:
- EXPERIMENT.yaml
- implementation.md
- config.yaml
checks:
- 任务只改变冻结的全局/局部得分路径组合，评估口径保持模板定义。
uncovered_scope:
- 真实 forward、loss 和 CUDA 行为须由服务器小跑确认。
