# V5-INNOVATION-002 质量检查

状态：`not_started`

当前只冻结检查项目，尚未启动训练，也没有任何指标可以放行。

## 开跑前

- [ ] 实验分支和唯一代码提交已经记录。
- [ ] 工作区为 clean，canonical 训练入口与四份 canonical V5 配置没有变化。
- [ ] 十份配置与参数矩阵逐行一致，重复任务指向正确。
- [ ] 数据、划分、类别顺序和输入文件身份一致。
- [ ] GPU 可见，没有冲突训练进程。
- [ ] 系统可用物理内存至少 14 GiB，足以装下约 9.84 GiB 特征缓存和运行开销。
- [ ] 目标 `RUN-xxx` 目录全部不存在。
- [ ] 模型、训练入口、运行边界和回归测试全部通过。

## 每个 RUN

- [ ] 退出码为 0。
- [ ] 没有 NaN、Inf 或 OOM。
- [ ] `training.log`、`metrics.json`、配置快照和运行身份齐全。
- [ ] 最佳模型与最后 checkpoint 存在且能对应本 RUN。
- [ ] U、S、H、ZS 与 best epoch 可读，配置和输入指纹能核对。

## 第一阶段门槛

- [ ] RUN-001 至 RUN-006 全部完成且证据完整。
- [ ] legacy 平均 H 落在 `74.17 ± 0.30`。
- [ ] 三组配对 `ΔH` 全部大于 0。
- [ ] 平均 `ΔH ≥ +0.50`。
- [ ] scale-consistent 的最小 H 高于 legacy 的最大 H。
- [ ] 平均 U 与平均 S 均未下降超过 `0.30`。

只有上面六项全勾选，才能启动 RUN-007 至 RUN-010。否则后四项必须记录为 `stage1_gate_failed_not_started`。

## 最终边界

- [ ] seed 5 的三次重复先求均值，再与 seed 17、29 等权汇总。
- [ ] 最终平均 `ΔH ≥ +0.50`，三个 seed 的方向为正且一致。
- [ ] 明确写出 `not_confirmation_evidence: true`，不冒充 confirmation 或 promotion。
- [ ] 失败与未启动任务均保留，不隐藏、不删除。
