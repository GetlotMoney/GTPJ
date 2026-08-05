# 修复回应

| 审核发现 | 修复 |
|---|---|
| 动态复跑未落成真实行 | 同步读取 `resolved_from_job_id`，回填真实 `DR-xxx`、完整指纹和参数变化。 |
| 不同版本误查重 | 查重键改为 `base_version + code_ref + config_fingerprint`。 |
| 运行缓存当作证据 | 完成/失败任务要求 `warehouse_dir`，写入 `artifact_ref`。 |
| CSV/阅读版可能脱节 | 增加刷新命令，校验和入账都会拒绝过期阅读版。 |
| 版本/模块结果可绕过表 | 两个正式结果入账命令均接入 ready matrix、目标行、seed 和配置核验。 |
| 指纹只靠人工填写 | 增加 `config_snapshot_ref` 和逐行 `freeze-parameter-matrix`。 |
| 复跑来源可伪造 | 本表和跨表来源都要求版本、代码引用、完整配置指纹相同。 |
| 多行无法逐行冻结 | freeze 只检查和保存当前行；所有行完成后再由整表 validate 放行。 |
