# V5-INNOVATION-021：忠实角色—Patch 证据（FRPE）

## 实验问题

冻结 CLIP 全局 CLS、576 个 patch 和 GPT-5.5-derived 八句，不训练 adapter；把每个角色的局部峰值相对图像平均响应作为最终分数的真实加数，能否提高同次 Mean8 的严格 GZSL H？

## 唯一改动

- 主条件：每角色 `top-8 patch mean - all-patch mean`，八项等权加入 Mean8。
- 唯一强度在 100/50 类不重叠 pseudo-GZSL 上从 `0.0..1.0` 冻结网格选择。
- 固定诊断：删除最高范数 patch、删除确定性随机 patch、只用 top-k 不减空间均值；三者共用主条件选出的强度，不参与选择。
- 不使用训练参数、PSE/RACE、检测器、OT、cross-attention、gamma 或 official-test 选参。

## 成功门

相对同次 Mean8：`delta_H >= 0.50`，且 U、S 任一项下降不超过 `0.50`。否则 `stop_no_gain`。

## Code Flow Diagram

```text
frozen CLS -> Mean8 base score ----------------------------+
frozen 576 patches + frozen 8-role text                    |
  -> role-wise patch cosine                                |
  -> top-8 mean minus spatial mean                         |
  -> exact eight additive score terms ---------------------+-> U/S/H/ZS
```
