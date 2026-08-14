# TE-PSE 来源与相关工作边界

## 直接来源

- `PAPER-2023-VDT-Adapter`：Enhancing CLIP with GPT-4: Harnessing Visual Descriptions as Prompts。
- 项目历史：`IDEA-0001_clip_a_self_text_prototype`、旧 PSE、SharedPSE、ABLATION-012/013。
- owner 对话候选：Transferable Evidence-Calibrated PSE，2026-08-15。

CLIP-A-self 使用同一类别内部的多句 Q/K/V self-attention、句子汇聚和 residual prototype，并在 base 类图像上训练 adapter。旧 PSE 与 SharedPSE 虽增加工程变化，仍保留该主骨架，必须作为来源和基线引用。

TE-PSE 删除句间 attention 与学习式 prototype 聚合。它固定寻找每个角色的跨类别最强语义 rival，把 target-minus-rival margin 直接写成最终分类 logit 的可审计加数，并只学习一个 seen/unseen 共享强度。

## 最接近的一手工作

- [ALBM，CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/html/Zhang_Attribute-formed_Class-specific_Concept_Space_Endowing_Language_Bottleneck_Model_with_Better_CVPR_2025_paper.html)：已有统一属性集合、每类每属性概念和逐属性加法；没有同角色 hard rival 与本项目的完整 GZSL 分解。
- [CODER，CVPR 2024](https://openaccess.thecvf.com/content/CVPR2024/html/Yi_Leveraging_Cross-Modal_Neighbor_Representation_for_Improved_CLIP_Classification_CVPR_2024_paper.html) 与 [Comparative Descriptors，WACV 2025](https://openaccess.thecvf.com/content/WACV2025/html/Lee_Enhancing_Visual_Classification_using_Comparative_Descriptors_WACV_2025_paper.html)：已有相似类别与成对比较描述；没有固定七角色的同角色 hard-rival 加法。
- [PC-CLIP，TMLR 2025](https://openreview.net/forum?id=USNJFZTWPn)：已有比较提示和有界差异原型；没有逐角色精确分解或 GZSL 对称公式。
- [Class-wise Matching Margin，2023](https://arxiv.org/abs/2310.03324)：已有自身匹配减最强 rival 的类别级 margin；不是冻结 CLIP 的逐图像逐角色分数修正。
- [DAZLE，CVPR 2020](https://openaccess.thecvf.com/content_CVPR_2020/html/Huynh_Fine-Grained_Generalized_Zero-Shot_Learning_via_Dense_Attribute-Based_Attention_CVPR_2020_paper.html)：已有逐属性加法与 GZSL；没有同角色文本 rival。

本轮最小检索未找到与完整 TE-PSE 公式等价的方法，但每个基础算子都有先例。后续论文贡献只能落在这组受约束的组合及其逐角色精确归因，不能落在单个算子。

## 可以声称的最小内容

只有实验支持后才可以写：

- 冻结 CLIP GZSL 中的 role-aligned hard-rival evidence correction；
- 文本可分性加权的逐图像 target-minus-rival margin；
- seen/unseen 共用一个有界强度；
- 每个角色贡献是最终 logit 的真实加数，支持精确删除检查。

## 当前不能声称

- 不能声称首次使用 comparative descriptor、nearest rival、正分数减最强负分数或逐属性加法。
- 不能声称 GPT 多句描述、CLIP 文本特征或 PSE 名称本身是本项目首创。
- 当前 q(c) 是文本静态一致度，不能写成动态或图像 confidence-aware calibration。
- 不能把文本 rival 当作视觉空间中的真实鸟类部位定位。
- 不能用 bias calibration 或 visual adapter 的后续收益证明 TE-PSE 本身有效。
- 未完成更广泛检索和真实实验前，不能写首次提出或 SOTA。
