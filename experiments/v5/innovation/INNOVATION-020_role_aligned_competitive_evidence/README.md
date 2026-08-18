# V5-INNOVATION-020：角色对齐竞争证据（RACE）

## 实验问题

在不训练、不移动类别原型的前提下，把每个角色对“目标类减同角色文本近邻类”的图像条件证据直接加入最终分数，能否比同次 GPT-5.5 八句 Mean8 提高严格 GZSL 的 H，同时不明显损伤 U 或 S？

## 唯一改动

- 基线：冻结 CLIP CLS 与 GPT-5.5-derived 八句 Mean8。
- RACE：固定完整 200 类同角色文本 rival 表；每个角色贡献为目标相似度减 rival 相似度。
- 不使用 QKV、prototype adapter、训练参数、patch、gamma 或 official-test 选参。
- 唯一强度 `lambda` 在 100/50 类不重叠 pseudo-GZSL 上从冻结网格选择，随后 official test 只评估一次。

## 成功门

相对同次 Mean8：`delta_H >= 0.50`，且 U、S 任一项下降不超过 `0.50` 个百分点。否则 `stop_no_gain`。

## Code Flow Diagram

```text
frozen CLS + frozen 8-role text
  -> Mean8 base score
  -> full-200 same-role text rival table
  -> per-role target-minus-rival evidence
  -> lambda selected on class-disjoint 100/50 validation
  -> base + exact additive role evidence
  -> official U/S/H/ZS once after selection state freeze
```

正式结果运行前保持在 `result.md` 的 pending 状态；运行资产写入外部 Warehouse，不写入 Git。
