# Evidence Quality Checker Output

role: `evidence_quality_checker`
agent_instance_id: `019f2cbb-c728-7731-be0e-151e1734dacf`
display_name: `CAMP-20260704-dr035-h76 | Evidence Quality Checker`
system_nickname: `Epicurus`
decision: allow_after_campaign_files_and_freeze

直接启动正式 Runner 被阻断，因为本轮 `CAMP-20260704-dr035-h76` 尚未有独立 campaign/attempt 证据文件，且当前工作树未提交。补齐 campaign 账本、ATTEMPT-008/009 预运行计划、agent runtime gate、机器验证和 freeze commit 后，可以进入正式 Runner。

正式归属：

- `ATTEMPT-008`: DR-035 六次 same-seed exact repeat。
- `ATTEMPT-009`: 100 个 existing-routing score search / tune。

必须避免：

- 不把 `ATTEMPT-004` 单次 `H=75.02` 写成 confirmed。
- 不把 `ATTEMPT-009` 单次高分直接写成 confirmed。
- 不复用旧 campaign 的 derived index 作为正式结果源。
- 不把 raw logs、checkpoints、summary 文件放进 Git。
- 不复用 runner 历史共享 `attempt-001/002/003` Warehouse 路径。
