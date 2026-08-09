# 质量检查

```text
experiment_id: V5-CONFIRM-003
run_commit: 47d91c5088dcc4a6b6d5e119e55c99894eff6147
formal_training: true
not_confirmation_evidence: true
decision: PASS_FOR_DIAGNOSTIC_ONLY
```

## 已核对

- [x] 母版固定为 `MODEL-V5-TEMPLATE-V1@2f5fa5e`，实际运行提交固定为 `47d91c5088dcc4a6b6d5e119e55c99894eff6147`。
- [x] 三行配置哈希均为 `def1d44cdee7ed4add7797637baf36b5715fc351068e0c154ac7f634cf2b7b9e`，且均为 seed=5。
- [x] 三次训练都来自干净工作树、独立进程和互不覆盖的输出目录，退出码均为 0。
- [x] 三份 `training.log` 的现场 SHA-256 与各自 `artifact_manifest.json` 一致。
- [x] 三份清单都记录 `status: completed`、准确运行提交、配置哈希、模型哈希和 12 项输入数据指纹。
- [x] `model_best.pth` 与对应完整 checkpoint 中的模型状态一致。
- [x] U/S/H/ZS 和最佳 epoch 已逐行回填，三次结果没有隐藏。
- [x] 互补性诊断只做训练后的解释；测试标签没有参与训练，也没有用于选择门控参数。
- [x] 首次启动的设备不一致失败保留在 `RUN-000-startup-failure/`，发生于 epoch 1 前，不计入三次正式运行。
- [x] 仓库只登记路径、哈希和轻量结果，没有加入原始日志或 checkpoint。

## 结论边界

三次独立进程的最终 H 均值为 `74.22829012836617`，范围为 `0.18350351823086442`。这能说明当前机器上同一配置的进程级波动较小，但三次都使用 seed=5，因此不能写成多 seed 稳定性确认，也不能据此升级 baseline、promotion 或论文中的稳定性结论。

局部分支单独预测的 H 均值只有 `1.5284`，但在全局分支出错的样本中仍有平均 `0.6482%` 被它预测正确。原融合相对全局分支 H 均值提高 `0.2577`，理想选择器上限相对全局提高 `0.7467`。这只支持“存在少量未被当前融合充分利用的互补信息”，不支持“局部分支本身是强分类器”。

## 已知风险

- `oracle` 使用标签做事后上限统计，不能作为可部署方法成绩。
- 训练目录还保留了中间 checkpoint；本次任务明确禁止修改或删除 `.runtime` 训练产物，因此未执行保留清理。后续如需清理，必须先由 owner 明确授权，并保留日志、最终指标、清单和最佳模型。
- 这里的 `PASS_FOR_DIAGNOSTIC_ONLY` 只表示训练和诊断证据可读、可追溯，不表示 confirmation 通过。
