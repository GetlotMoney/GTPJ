# 实现说明

## 四个训练方案

1. `fgvd_off`：保留 FGVD top-k 与 `embed_cv`，只跳过几何关系和几何编码器。
2. `local_ce`：在 1 的基础上增加 `0.1 * CE(local_seen, y)`。
3. `confusion_contrast`：在 2 的基础上，用 detached global logits 选 5 个最难负类，
   增加权重 `0.1`、margin `0.1` 的局部排序损失。
4. `crop_distill`：在 2 的基础上，读取两份真实 `RandomResizedCrop` CLS 缓存，
   用裁剪全局预测的平均分布蒸馏局部分数，权重 `0.05`、温度 `2.0`。

## 推理方案

方案 5 先用 global logits 固定 top-5，再将候选内 local logits 居中、按最大绝对值
归一化，并加入最大幅度 `0.25` 的 `tanh` 残差。候选外类别永远不能被局部提升。

## 不变边界

CLIP 缓存、xlsa17 划分、类别顺序、优化器、50 epoch 日程和 U/S/H/ZS 计算不变。
