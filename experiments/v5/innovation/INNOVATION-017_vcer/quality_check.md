# V5-INNOVATION-017 质量检查

```text
status: pass_for_failure_record
decision: reject
promotion_decision: rejected
```

- 代码与配置：run commit、config SHA 与两轮 Runner 审核绑定一致，审核均为 pass、blocker=0。
- 数据：训练/official cache、X2 checkpoint、划分和 200 类顺序均通过冻结 SHA hard gate。
- 训练：固定 seed 5、50 epoch；checkpoint 不由 official 指标选择。
- 评估：seen/unseen 在 200 类竞争；旧 Runner 对动态-rival ZS 错用了 200 类前向切列。
  修复 commit `eb54c006` 已通过两轮新审核，并用原 checkpoint 对四组条件分别执行
  fresh 50-unseen-class 前向；原 U/S/H 不变，旧的三个 VCER 路径 ZS 作废。
- 产物：50 个 epoch 日志、metrics 和 checkpoint 存在，SHA-256 已实算，日志无 traceback。
- 修复产物：独立 correction 目录内 `zs_metrics.json` 与 `evaluation.log` 已实算 SHA；
  原 `RUN-001` 的日志、metrics、checkpoint 三个 SHA 在修复后保持不变。
- 结论边界：这是 owner 指定的 official-test-guided development，不是 confirmation 或 promotion 证据。
- 已知缺口：启动器未持久化数值退出码，账本如实留空。
