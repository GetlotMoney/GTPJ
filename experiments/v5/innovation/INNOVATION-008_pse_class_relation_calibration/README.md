# V5-INNOVATION-008：PSE 类别关系增强与 GZSL 自校准

## 当前结论

五组 seed 5 计划已经冻结到参数表，代码实现已完成针对性单元测试，但真实训练尚未启动。E4 的 `gamma` 仍为空；在类不重叠验证划分准备好之前，E4 不得运行。

```text
experiment_id: V5-INNOVATION-008
idea_id: IDEA-0007
base_template_id: MODEL-V5-TEMPLATE-V1
base_template_tag: model/v5-template-v1
base_template_commit: 2f5fa5e631ef82658d4bac587cdfd17f3534cb35
code_branch: exp/v5/innovation/innovation-008-pse-class-relation-calibration
seed_first_pass: 5
run_commit: pending_pre_run_freeze
status: implementation_ready_for_review
```

## 实验问题

旧 PSE 的注意力发生在“同一类别的多条句子”之间，不发生在类别之间。反事实探针证明：修改类别 A 后，其他类别输出最大变化为 `0.0`。本实验依次回答：真正的类别关系、未见原型的一致处理、训练期温和校准和推理期判决线校准各自能带来什么。

## 五组运行

| RUN | 组别 | 配置 | 当前状态 |
|---|---|---|---|
| RUN-001 | E0 新公平基线 | `config.yaml` | planned |
| RUN-002 | E1 修复类别自注意力 | `configs/E1_fix_class_attention.yaml` | planned |
| RUN-003 | E2 未见类共享 PSE | `configs/E2_shared_unseen_pse.yaml` | planned |
| RUN-004 | E3 训练期概率下限 | `configs/E3_training_self_calibration.yaml` | planned |
| RUN-005 | E4 推理期 calibrated stacking | `configs/E4_calibrated_stacking.yaml` | 等待验证集 gamma |

每个训练 RUN 使用独立输出目录，例如：

```powershell
conda run -n dvsr_gpu python train_GTPJ_CUB.py `
  --config experiments/v5/innovation/INNOVATION-008_pse_class_relation_calibration/config.yaml `
  --output-dir D:/Backup/Documents/Myself/GTPJ_Warehouse/runs/V5-INNOVATION-008/RUN-001
```

新运行若输出目录已存在会直接停止，避免覆盖旧结果。目录内至少产生 `training.log`、`checkpoint_last.pth`、`model_final.pth` 和 `metrics.yaml`。

## 公平比较口径

- 数据、50 个 epoch、学习率阶段、batch size 和 seed 相同。
- 批次采样使用独立 CPU generator，并随 checkpoint 保存和恢复。
- 大文件首次完整 SHA-256，后续只在路径、文件身份、大小或高精度修改时间变化时重算。
- 交叉熵只看已见类；未见类图片和标签不进入训练。
- 每个训练 RUN 固定训练完后只评估一次测试集，不按测试 H 挑 epoch。

因此，E0 是本实验的新公平基线。历史 `confirmed_H=74.44` 来自旧的“逐 epoch 测试并选最佳”口径，只作背景参考，不能与新 E0 直接做等价比较。

## 第一阶段判定

- 先完成 E0–E3 的 seed 5；E4 不训练，复用 E2。
- 最佳训练方案再与 E0 做 seed 5、17、29 成对复现。
- 目标是平均 H 至少提高 0.20，且不能靠 S 明显下降换 U。
- E4 只能写成推理判决线收益，不能写成 PSE 表示学习收益。

## 文件入口

- 机器参数表：`PARAMETER_MATRIX.csv`
- 人读参数表：`PARAMETER_MATRIX.md`
- 实现说明：`implementation.md`
- 方法来源：`module_source.md`
- 可编辑框架图：`framework_diagram.drawio`
- 本地浏览图：`framework_diagram.html`
- Markdown 权威图：`framework_diagram.md`
