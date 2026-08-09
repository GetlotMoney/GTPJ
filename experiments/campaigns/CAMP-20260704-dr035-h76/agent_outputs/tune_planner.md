# Tune Planner Output

role: `tune_planner`
agent_instance_id: `019f2cbb-fefc-7170-acfc-cd953daf8b8c`
display_name: `CAMP-20260704-dr035-h76 | Tune Planner`
system_nickname: `Linnaeus`
decision: allow

建议先跑 DR-035 min6，把 ATTEMPT-007 的 min3 扩展到六次。之后再跑 100 个 existing-routing 调参实验，重点集中在 `direction_sample_h48` 附近，同时少量探索 `local_gate`、`pse_gate=class` 和 `direction+local/PSE` 组合。

规划原则：

- `batch_size=64`，不再打开 bs=128。
- `dynamic_icsa_mode` 默认固定；只允许极少量低比例 guarded probe。
- `dynamic_pse_mode=sample` 禁止。
- 单次高分只进入 `tune_promising`；需要 min3/min6 才能升级为 confirmed candidate。

本轮 helper profile：

- `dr035-min6-confirm`: 6 个 DR-035 same-seed repeat。
- `h76-existing-routing-100`: 100 个已有动态路由开关组合。
