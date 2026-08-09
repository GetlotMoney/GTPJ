# 模块来源说明

## 结论

本实验唯一新增机制是“尺度一致的最终融合”。局部分支本身及其内部模块全部继承自 `MODEL-V5-TEMPLATE-V1`，不能写成本实验首创。

## 直接来源

| 内容 | 来源 | 本实验是否新建 |
|---|---|---|
| CLIP 图像/文本编码与 `logit_scale` | `model/v5-template-v1` | 否 |
| PSE、ICSA、BVSA、FGVD、SGMP | `model/v5-template-v1` | 否 |
| `global_logits` 与 `local_logits` | `model/v5-template-v1:model/MyModel.py` | 否 |
| legacy 公式 `global + 0.2 * local` | `model/v5-template-v1:model/MyModel.py` | 否，原样保留 |
| scale-consistent 公式 `global + 0.05 * logit_scale * local` | `IDEA-0004` / 本实验分支 | 是，本实验唯一新机制 |

## 为什么提出这个改动

冻结母版里，`global_logits` 是归一化视觉特征与文本特征的余弦相似度，再乘 `clamp(exp(logit_scale), max=100)`；`local_logits` 是局部路径输出的余弦分数，没有乘同一温度尺度。二者直接相加时，局部项的实际影响可能远小于配置表面上的 `0.2`。

`V5-ABLATION-001` 的完成结果提供了第二个观察：完整 V5 相对干净无局部版本的三个同 seed H 差值为 `+0.25/-0.09/+0.09`，平均仅 `+0.08`。这不能证明局部信息没有用，也不能证明尺度修复有效；它只支持做一次严格配对检验。

## 创新边界

- 可以说：本实验检验“全局/局部分数尺度不一致是否压低局部贡献”。
- 可以说：本实验增加固定系数、温度对齐的最终融合方式。
- 不可以说：本实验发明了 CLIP、PSE、ICSA、BVSA、FGVD、SGMP 或局部分支。
- 不可以在结果出来前说该机制提高了 H。

## 证据锚点

- 冻结母版：`model/v5-template-v1`，代码提交 `2f5fa5e631ef82658d4bac587cdfd17f3534cb35`。
- 母版登记：`7da3c72a060510ad35dd66d839cbe22569b3d8cf:experiments/v5/TEMPLATE.yaml`。
- 完成消融：`main@4f29e99bb1a940afa66bb66f8150c379c2d0af7f:experiments/v5/ablation/ABLATION-001_local_branch_effect/result.md`。
- Idea：`idea_tree/ideas/IDEA-0004_scale_consistent_fusion/IDEA.md`。
