# 协作摘要

```text
experiment_id: V5-INNOVATION-008
base_version: v5
code_branch: exp/v5/innovation/innovation-008-pse-class-relation-calibration
activation_mode: implementation_with_bounded_read_only_support
formal_training_started: false
memory_used: false
verified_against_current_repo: true
final_decision: pending_real_runs
```

## 主实现

- 责任：读取现有 V5 代码和项目规则，完成 E0–E4 的最小实现、配置、测试和账本。
- 写入范围：`model/MyModel.py`、`train_GTPJ_CUB.py`、`tools/v5_*`、实验目录、idea_tree 和必要项目文档。
- 当前结论：实现测试通过；真实 CUDA 运行和指标尚未产生。

## 只读方法核对

- 范围：训练期 self-calibration 与推理期 calibrated stacking 的原论文和作者代码。
- 发现：DAZLE 原式与本实验 seen-only CE 直接组合会产生持续抬高未见类概率的风险；因此采用达到固定下限后归零的有界版本，并在文档中明确写为 DAZLE-inspired。
- 推理结论：E4 使用 `seen logits -= gamma`，gamma 只从类不重叠验证划分确定。
- 文件写入：无。

## 独立代码审核

- 审核轮数：1 轮，原因是改动触及模型、loss 和 eval 语义，但范围只在一个实验分支。
- Reviewer：独立只读 Agent，只复核当前实现，不改文件。
- 审核结论：`PASS`。首轮发现续训可跨 RUN 混写；修复为 checkpoint 必须位于当前输出目录后复核通过，无剩余开跑阻断。
- 未覆盖：真实 CUDA 训练与 E4 验证集选 gamma，分别由本轮运行和后续 E4 配套验证。
