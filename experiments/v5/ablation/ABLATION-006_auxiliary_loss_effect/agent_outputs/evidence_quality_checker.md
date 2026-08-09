role: evidence_quality_checker
subject_id: V5-ABLATION-006
decision: allow
files_reviewed:
- DATA_MANIFEST.json
- PARAMETER_MATRIX.csv
- quality_check.md
checks:
- 指标列仍为空，没有提前伪造结果。
- 数据文件、配置和提交必须在任务领取前逐项重算哈希。
- 本轮标记 not_confirmation_evidence，不可直接晋级框架。
uncovered_scope:
- Warehouse 收据、日志哈希和最终指标须在训练后回填。
