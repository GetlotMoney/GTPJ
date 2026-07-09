# Evidence Quality Checker

role_key: evidence_quality_checker
execution_mode: role_only
status: allow

检查结论：ATTEMPT-012 有正式 ledger 行、manifest、pre-run plan、agent runtime gate、role outputs、quality skeleton 和 monitor handoff。结果验收必须以服务器 `batch_status.json`、`events.jsonl`、`summary.csv`、`summary.jsonl` 和 controller logs 为准，不用目录存在与否判断完成状态。
