# V5-INNOVATION-002 质量检查

状态：`completed_stage1_gate_failed`

## 开跑前

- [x] 实验分支和唯一代码提交已经记录：`f6335558b73b1ce4d3ef8174add18b9bb8bf96d2`。
- [x] 每个正式 RUN 启动时工作区为 clean，canonical 训练入口与四份 canonical V5 配置没有变化。
- [x] 十份配置与参数矩阵逐行一致，重复任务指向正确。
- [x] 数据、划分、类别顺序和输入文件身份一致。
- [x] GPU 可见，没有并行冲突训练进程。
- [x] 每次创建 RUN 前均通过 14 GiB 可用物理内存门；低内存尝试在建目录前被拒绝。
- [x] `RUN-001` 至 `RUN-006` 各自启动前目录不存在，没有覆盖历史。
- [x] 模型、训练入口、运行边界和 74 项回归测试全部通过。

## 每个 RUN

- [x] `RUN-001` 至 `RUN-006` 退出码均为 0。
- [x] 六轮均没有 NaN、Inf 或 OOM。
- [x] 六轮的 `training.log`、`metrics.json`、配置快照和运行身份齐全。
- [x] 六轮的最佳模型与最后 checkpoint 存在且能对应本 RUN。
- [x] 六轮 U、S、H、ZS 与 best epoch 可读，配置和输入指纹能核对。

## 第一阶段门槛

- [x] RUN-001 至 RUN-006 全部完成且证据完整。
- [x] legacy 平均 H=`74.129866`，落在 `74.17 ± 0.30`。
- [ ] 三组配对 `ΔH` 全部大于 0；实际为 `-3.190918/-2.917551/-2.978006`。
- [ ] 平均 `ΔH ≥ +0.50`；实际为 `-3.028825`。
- [ ] scale-consistent 的最小 H 高于 legacy 的最大 H；实际 `70.953464 < 74.202218`。
- [ ] 平均 U 与平均 S 均未下降超过 `0.30`；U 下降 `7.101174`，S 提升 `2.102218`。

只有上面六项全勾选，才能启动 RUN-007 至 RUN-010。当前四项失败，后四个目录已核对为不存在，并记录为 `stage1_gate_failed_not_started`。

## 最终边界

- [x] Stage 1 失败后停止，没有把 seed 5 重复错误冒充跨 seed 结论。
- [x] 明确写出 `not_confirmation_evidence: true`，不冒充 confirmation 或 promotion。
- [x] 失败与未启动任务均保留，不隐藏、不删除。
- [x] 独立只读审核重新取数并给出 `Stage 1 FAIL / block`，与主计算一致。
