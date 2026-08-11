# ABLATION-010_pse_icsa_interaction

本实验只回答一个问题：同时关闭 PSE 与 ICSA 后，完整 V5 的 U、S、H、ZS 如何变化。它是两种子双重复的筛查，不是正式确认实验。

## 固定条件

- 母版：`model/v5-template-v1`，提交 `2f5fa5e631ef82658d4bac587cdfd17f3534cb35`。
- 代码快照：`7e1592cf832546dd3ebb8a1d0331c12fbcbdd69e`。
- 改动：`ablation_disable_pse=true`、`ablation_disable_icsa=true`，并将失去梯度作用的 `lambda_topo_pearson` 显式设为 `0.0`。
- PSE 关闭后，seen 文本直接使用句子向量均值并归一化。
- ICSA 关闭后，类别文本不再加入图像条件偏移。
- PSE 关闭后，原 topology 只依赖固定文本，无法再约束可训练参数，因此本实验同时关闭这项 PSE-dependent topology；不重新设计替代拓扑。
- FGVD、BVSA、SGMP、局部融合、CE、consistency、BMDD、MPP、negative semantic、数据、类别顺序、训练日程和评估公式保持不变。
- RUN：seed 5、17，各独立运行两次；物理 GPU 1，进程内使用逻辑 `cuda:0`。

## 对照规则

每个 RUN 只与 `V5-ABLATION-008` 中相同 seed、相同重复编号的 `GL-FULL` 比较。不能复用其他种子，也不能把四次筛查平均数写成稳定确认。

## 启动边界

正式运行只允许由冻结后的 `CAMP-20260809-v5-ablation100` 后台控制器在 GPU 1 上串行启动。控制器完成前不可手工正式启动；单独调用训练入口得到的结果不能回填本表。

## 当前状态

- 运行前代码和参数表正在冻结。
- 审核尚未完成。
- `manifest.yaml`、`result.yaml`、`result.md` 和 `quality_check.md` 只能在训练完成后生成。
