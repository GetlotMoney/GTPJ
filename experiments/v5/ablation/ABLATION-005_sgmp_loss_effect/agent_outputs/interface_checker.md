role: interface_checker
subject_id: V5-ABLATION-005
decision: allow
files_reviewed:
- EXPERIMENT.yaml
- implementation.md
- config.yaml
checks:
- 数据划分、类别顺序与 U/S/H/ZS 口径未在本实验账本中改写。
- 实验修改范围与说明一致；运行前仍由准确提交和 source hash 再核对。
uncovered_scope:
- 真实 forward、loss 与 CUDA 行为须在服务器小跑确认。
