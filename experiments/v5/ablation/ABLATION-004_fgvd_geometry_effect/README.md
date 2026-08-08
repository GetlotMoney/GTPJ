# ABLATION-004_fgvd_geometry_effect

本实验只回答一个问题：保留原始 top-K 选择和完整局部分支，只旁路 FGVD 几何编码后，V5 的 U、S、H、ZS 如何变化。它是两种子双重复筛查，不是正式确认实验。

## 固定条件

- 母版：`model/v5-template-v1`，提交 `2f5fa5e631ef82658d4bac587cdfd17f3534cb35`。
- 代码快照：`024474b12f3954355193dbcabd1905ba8218cda2`。
- 唯一改动：`ablation_disable_fgvd_geometry=true`。
- 原始 `fgvd_select_patches`、`fgvd_select_k=32` 和 `embed_cv` 保持不变。
- 旁路后 `fgvd_memory` 直接等于投影后的 selected patches；不计算 patch 几何，也不调用 `fgvd_encoder`。
- BVSA 的 v2s/s2v、SGMP、局部融合、全部损失、PSE、ICSA、数据、类别顺序、训练日程和评估公式保持不变，`lambda_topo_pearson=0.1`。
- RUN：seed 5、17，各独立运行两次；物理 GPU 1，进程内使用逻辑 `cuda:0`。

## 对照规则

每个 RUN 只与 `V5-ABLATION-008` 中相同 seed、相同重复编号的 `GL-FULL` 比较。不能把四次筛查平均数写成稳定确认。

## 启动边界

正式运行只允许由冻结后的 `CAMP-20260809-v5-ablation100` 后台控制器在 GPU 1 上串行启动。控制器完成前不可手工正式启动；单独运行训练入口得到的结果不能回填本表。

## 当前状态

- 运行前代码和参数表正在冻结。
- strict-3 审核尚未完成。
- `manifest.yaml`、`result.yaml`、`result.md` 和 `quality_check.md` 只能在训练完成后生成。
