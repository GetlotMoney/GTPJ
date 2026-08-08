# 证据质量检查

role_key: evidence_quality_checker
execution_mode: role_only
formal_runtime_backend: server_detached_role_only
decision: allow

files_reviewed:
- EXPERIMENT.yaml
- PARAMETER_MATRIX.csv
- DATA_MANIFEST.json
- quality_check.md
- SERVER_RECOVERY.md
- docs/agent_reviews/2026-08-07-v5-local-ablation

检查结论：当前只允许生成“局部分支完整移除后的配对消融”证据，不允许提前写入精度结论、确认结论或论文主张。六个 RUN 必须分别拥有启动收据、结束收据、完整训练日志和结果制品；任何 PID、日志哈希、配置哈希、数据指纹或退出码不一致都阻断正式证据。配对差值必须同时报告三个 seed 的逐对结果、均值和波动。
