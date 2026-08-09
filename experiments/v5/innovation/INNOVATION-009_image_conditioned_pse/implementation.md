# 实现记录

## 输入与输出

| 名称 | shape | 含义 |
|---|---|---|
| `clip_features` | `[B,577,768]` | 1 个 CLS 加 576 个局部块 |
| `all_enhanced` | `[200,8,768]` | seen/unseen 共用 PSE 后仍保留的 8 句 |
| `sentence_weights` | `[B,200,8]` | 每张图片、每个候选类别的句权，末维和为 1 |
| `image_conditioned_text` | `[B,200,768]` | 图像条件类别原型 |
| `uniform_text` | `[200,768]` | seen/unseen 同路的均匀 PSE 原型，供 BVSA 和 SGMP 使用 |
| `topology_text` | `[200,768]` | 母版原输入：seen 使用 PSE 均值，unseen 使用原始均值 |
| `final_logits` | `[B,200]` | `global_logits + 0.2 * local_logits` |

## 梯度与损失

主分类损失通过全局分数更新 PSE 和 logit scale；局部 BVSA 不读取条件句权。原有 final CE、global→local KL、topology、BMDD、MPP 和 negative loss 的公式及权重保持不变。拓扑仍读取母版的静态 `[C,D]` 输入，即 seen 的 PSE 均值加 unseen 的原始均值，不读取 `[B,C,D]` 条件原型。

## 基线关闭

`interaction_mode=v5_baseline` 时实例化原 ICSA 并恢复 V5 前向路径；active 模式不实例化 ICSA。两种模式保持 logits shape、类别顺序、标签映射和评估接口不变。

## 最低验证

- 8 句权重和为 1；
- CUDA 类别编号在 CPU logits 上评估时会先统一到 CPU，避免跨设备索引；
- 均匀权重严格退化到 PSE 均值；
- 固定 patches、只改变 CLS 时 local logits 不变；
- train/eval 类别轴分别为 seen/all；
- 全部既有 loss 有限并能反传；
- 大文件身份未变时不重复完整 SHA-256。
