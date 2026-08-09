# Evidence Quality Checker

role_key: evidence_quality_checker
execution_mode: role_only
formal_runtime_backend: server_detached_role_only
status: allow

summary: ATTEMPT-014 必须按 exact-repeat 规则运行：原 seed、原配置、每候选最多 5 次，只有达到 per-job `restore_target_H` 才算还原；promotion 保持 blocked。
