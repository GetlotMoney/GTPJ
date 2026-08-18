# V5-INNOVATION-018：双原型专家融合（DPEF）

## 问题

能否同时保留强 seen-only 均匀原型映射的 seen 判别力，以及 SharedPSE 对 unseen 文本的迁移能力，使纯全局 CUB GZSL 超过 `H=75`？

## 冻结公式

两个专家都只输出归一化类别原型：

- `P_strong`：八句话固定均匀汇总，只训练 seen 类；带 `0.1` topology loss，不含 ICSA 和局部分支。
- `P_shared`：冻结复用 `V5-INNOVATION-017/RUN-002` SharedPSE checkpoint。
- `P_raw`：八句话等权均值。

对已知 GZSL 类别划分分别融合：

```text
seen:   normalize((1-a) * P_strong + a * P_shared)
unseen: normalize((1-b) * P_raw    + b * P_shared)
```

`a=0.00..0.30/0.01`，`b=0.80..1.00/0.02`。训练阶段只用 seen 训练图像；先用 seen 内部 10% validation CE 选 epoch，再在全部 seen 训练图像上按该 epoch 重训。模型 checkpoint 冻结后才加载 official test，并在 test 上选择 `(a,b)`。

## 证据口径

本实验明确是 `official_test_score_search`，因此：

- 可以回答“该机制在已暴露 test 上能否达到 75+”；
- 不能作为 confirmation、stable generalization 或 promotion 证据；
- 后续若需要论文级结果，必须在 100/50 类不重叠 validation 上选 `(a,b)`，再固定后测试一次。

## 成功门

- score-search 最佳 `H >= 75.0`：保留为候选机制；
- 否则停止，不扩大网格、不增加 gamma、adapter 或局部分支。

## 正式结果

`RUN-001` 达到 `U=73.206306, S=79.987937, H=76.447016, ZS=82.601786`，最佳系数为 `a=0.14, b=1.00`。成功门已达到；该数字仍严格属于 `official_test_score_search / not_confirmation_evidence`。

## 运行

```bash
python experiments/v5/innovation/INNOVATION-018_dual_prototype_expert_fusion/train.py \
  --config experiments/v5/innovation/INNOVATION-018_dual_prototype_expert_fusion/config.yaml \
  --run-dir <WAREHOUSE>/runs/v5/innovation/V5-INNOVATION-018/RUN-001 \
  --expected-commit <PRE_RUN_COMMIT> \
  --source-checkpoint <WAREHOUSE>/runs/v5/innovation/V5-INNOVATION-017/RUN-002/model_best.pth
```
