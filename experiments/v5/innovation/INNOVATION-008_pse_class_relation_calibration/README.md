# V5-INNOVATION-008：PSE 类别关系增强与 GZSL 自校准

## 当前结论

第一版已经按停止条件收口：公平基线 E0 为 `H=73.69`；E1 为 `H=66.92`，虽然 `U` 增加 7.50，但 `S` 下降 18.13。诊断确认，名义 `0.1` 的修正实际平均达到原型的 `2.94` 倍，而且只改变 seen 原型。

2026-08-10 经 owner 批准后启动第二版。第二版不抹掉第一版失败记录，只测试三个更干净的问题：R0 验证基线、R1 未见类共享旧句子 PSE、R2 在 R1 上增加限幅且从恒等映射开始的类别关系注意力。训练校准和推理校准暂缓。

```text
experiment_id: V5-INNOVATION-008
idea_id: IDEA-0007
base_template_id: MODEL-V5-TEMPLATE-V1
base_template_tag: model/v5-template-v1
base_template_commit: 2f5fa5e631ef82658d4bac587cdfd17f3534cb35
code_branch: exp/v5/innovation/innovation-008-pse-class-relation-calibration
seed_first_pass: 5
run_commit: pending_redesign_pre_run_commit
status: redesigned_validation_pending
```

## 实验问题

旧 PSE 的注意力发生在“同一类别的多条句子”之间，不发生在类别之间。反事实探针证明：修改类别 A 后，其他类别输出最大变化为 `0.0`。本实验依次回答：真正的类别关系、未见原型的一致处理、训练期温和校准和推理期判决线校准各自能带来什么。

## 五组运行

以下 E0–E4 是第一版历史，不再续跑：

| RUN | 组别 | 配置 | 当前状态 |
|---|---|---|---|
| RUN-001 | E0 新公平基线 | `config.yaml` | failed：首个 epoch 前 CUDA 设备检查错误 |
| RUN-002 | E1 修复类别自注意力 | `configs/E1_fix_class_attention.yaml` | completed：H=66.92，否决 |
| RUN-003 | E2 未见类共享 PSE | `configs/E2_shared_unseen_pse.yaml` | skipped：E1 未过门 |
| RUN-004 | E3 训练期概率下限 | `configs/E3_training_self_calibration.yaml` | skipped：E1 未过门 |
| RUN-005 | E4 推理期 calibrated stacking | `configs/E4_calibrated_stacking.yaml` | skipped：没有 E2 checkpoint |
| RUN-006 | E0 CUDA 修复后重跑 | `config.yaml` | failed：完成 50 epoch 后最终评估设备错误 |
| RUN-007 | E0 评估设备修复后重跑 | `config.yaml` | completed：H=73.69 |

## 第二版三组验证

三组都只使用 xlsa17 的 `train_loc/val_loc`：100 个 pseudo-seen 类中每类固定留出 20% 图片，50 个 `val_loc` 类作为 pseudo-unseen。正式 `test_seen/test_unseen` 缓存不会加载。

| RUN | 组别 | 唯一变化 | 配置 | 状态 |
|---|---|---|---|---|
| RUN-008 | R0 | 旧句子 PSE 验证基线 | `configs/R0_validation_legacy.yaml` | planned |
| RUN-009 | R1 | unseen 也经过同一个旧句子 PSE | `configs/R1_validation_shared_sentence_pse.yaml` | planned |
| RUN-010 | R2 | R1 加限幅、零起点类别关系注意力 | `configs/R2_validation_safe_class_relation.yaml` | planned |

R0、R1、R2 都会跑完；不会再用“seen-only 中间组失败”提前取消恰好用于修复不一致的下一组。只有验证集上的 R2 通过门槛，才会另行冻结正式测试配置。

每个训练 RUN 使用独立输出目录，例如：

```powershell
conda run -n dvsr_gpu python train_GTPJ_CUB.py `
  --config experiments/v5/innovation/INNOVATION-008_pse_class_relation_calibration/configs/R0_validation_legacy.yaml `
  --output-dir D:/Backup/Documents/Myself/GTPJ/.runtime/runs/V5-INNOVATION-008/RUN-008
```

新运行若输出目录已存在会直接停止，避免覆盖旧结果。目录内至少产生 `training.log`、`checkpoint_last.pth`、`model_final.pth` 和 `metrics.yaml`。

## 公平比较口径

- 数据、50 个 epoch、学习率阶段、batch size 和 seed 相同。
- 批次采样使用独立 CPU generator，并随 checkpoint 保存和恢复。
- 大文件首次完整 SHA-256，后续只在路径、文件身份、大小或高精度修改时间变化时重算。
- 交叉熵只看已见类；未见类图片和标签不进入训练。
- 每个训练 RUN 固定训练完后只评估一次对应划分；R0–R2 只评验证划分，不按 H 挑 epoch，也不读取正式测试缓存。
- 训练和验证按位置逐 batch 从同一份 patch 缓存取数，不复制整份大缓存。

因此，E0 是本实验的新公平基线。历史 `confirmed_H=74.44` 来自旧的“逐 epoch 测试并选最佳”口径，只作背景参考，不能与新 E0 直接做等价比较。

## 第一阶段判定

- 先完成 R0–R2 的类不重叠验证，正式测试集不参与选择。
- R2 的实际修正范数必须不超过 `0.1`，原型旋转角必须不超过约 `5.75°`。
- 验证通过后，才冻结正式 R0/R2 的 seed 5；seed 5 通过再补 seed 17、29。
- 正式三 seed 要求平均 H 至少提高 0.20，三次 H 都高于对应基线，且不能靠 S 明显下降换 U。
- 自校准和 calibrated stacking 不属于本轮，避免掩盖原型表示问题。

## 文件入口

- 机器参数表：`PARAMETER_MATRIX.csv`
- 人读参数表：`PARAMETER_MATRIX.md`
- 实现说明：`implementation.md`
- 方法来源：`module_source.md`
- 可编辑框架图：`framework_diagram.drawio`
- 本地浏览图：`framework_diagram.html`
- Markdown 权威图：`framework_diagram.md`
