# ARTV 模块来源

## 结论

ARTV（Anatomy-Anchored Role Transport Verifier，解剖锚定角色传输验证器）来自
Owner 与 Codex 于 2026-08-17 针对 X2 top-2 错误结构的共同设计，不是外部代码复现。
PSE-X2 仍只是冻结母体，不作为本实验的原创声明。

## 直接来源

- 创意节点：`IDEA-0015`
- 来源标识：`owner-codex:2026-08-17:ARTV_crop_grounded_top2_verifier`
- 固定底座：`PSE-X2@a0ac9d8f82fef6022da5e823049b00760cd1fa2e`
- 冻结 checkpoint SHA-256：`a0d8465d3a716ec52d197c8ca10ab9e70dff73d09fe56099e38d8270ee7243f3`
- 实现文件：`artv.py`；正式入口：`evaluate.py`

## 为什么需要它

X2 已经能把真实类别放进前两名，却经常把第二名排在第一名。ARTV 不重新学习
200 类分类器，只回答一个更窄的问题：六个局部部位、一个全局描述和一个独特描述，
是否共同提供了足够证据把 X2 的第一、第二名交换。

## 八句话的职责

| 句子 | 数量 | 职责 |
|---|---:|---|
| beak/head/body/wings/tail/legs | 6 | 分别给对应视觉槽投一票 |
| overall appearance | 1 | 对 top-2 成对、对称地估计前景裁剪质量 |
| unique discriminative features | 1 | 跨六个视觉槽投第七票 |

第八句是后来生成的独特特征句，不描述为历史恢复的原始第八句。

## 与旧路线的边界

- 不继承失败的 VCER、CHORM、RBD、BRVM、RC-GDT、DCRA 或 DPEF 修正。
- 不使用旧 patch cache，不训练 Adapter，不引入 gamma、类别参数或 split 参数。
- 不改变 X2 的其余 198 个类别分数；证据不足时精确返回 X2。
