# 证据索引

状态：`completed_reviewed`。

## 直接结果

- 三种子配对指标和结论：[`../result.md`](../result.md)；
- 每次真实训练的参数、收据、日志哈希和 Warehouse 位置：[`../PARAMETER_MATRIX.csv`](../PARAMETER_MATRIX.csv)；
- 逐任务参数阅读版：[`../PARAMETER_MATRIX.md`](../PARAMETER_MATRIX.md)；
- 数据、split、类别顺序和评估输入身份：[`../DATA_MANIFEST.json`](../DATA_MANIFEST.json)；
- 质量门、失败历史和运行后复核：[`../quality_check.md`](../quality_check.md)。

FULL 与 GLOBAL_ONLY 各完成 seed 5、17、29。FULL 平均 H 为 `74.11`，GLOBAL_ONLY 平均 H 为 `74.03`，配对平均差值为 `+0.08`；结论是未观察到稳定 H 增益，而不是“局部分支绝对无效”。

## 审核与历史来源

- 训练后 strict-3 审核包：`docs/agent_reviews/2026-08-08-v5-local-ablation-final-results/`；
- 完整实验代码、运行专属控制器和早期审核证据保留在 `exp/v5/ablation/ablation-001-local-branch-effect@b91da7e612303b4375a39df54f9531f728530bea`；
- 旧探索来源仅用于回查：`codex/attempt019-local-ablation#ATTEMPT-019@954851b0d2dfd2d23f1efca10ba1bf142b3a6d68`。

原始日志、checkpoint、运行时目录和数据快照继续保存在 Warehouse，不进入 Git。
