# VCER 模块来源

## 结论

VCER（Visibility-aware Counterfactual Evidence Routing，可见反事实证据路由）来自
Owner 于 2026-08-16 对当前 CUB 严格 GZSL 问题的框架设计，不是某篇论文或外部代码的复现。
本实现没有复制外部模块代码。

## 直接来源

- 创意节点：`IDEA-0014`
- 来源标识：`owner:2026-08-16:VCER_6local_unique_router_global_foreground`
- 固定母体：`PSE-X2`，历史实现参考 commit
  `d44bf2e8c9b472a671012a70978e8132049795ee`
- 当前实现：`vcer.py`

PSE-X2 只作为冻结的强文本原型和全局余弦底分。VCER 的新增内容是：针对每张图、
每个候选类动态选择其最强混淆类，再把文本角色的明确分工转化为局部视觉反事实证据。
因此，PSE-X2 不是本实验的原创声明，VCER 才是待验证的新模块。

## 八句的真实语义结构

八句不是八条对称分支，而是三种职责：

| 索引 | 角色 | VCER 中的职责 |
|---:|---|---|
| 0 | beak | 局部证据 |
| 1 | head_features | 局部证据 |
| 2 | body_plumage | 局部证据 |
| 3 | wings | 局部证据 |
| 4 | tail | 局部证据 |
| 5 | legs | 局部证据 |
| 6 | overall_appearance | 主体/前景可见性 |
| 7 | unique_discriminative_features | 把类别差异路由到六个局部角色 |

第八句是后来生成的独特特征句；本记录不把它描述成历史恢复的原始第八句。

## 与已失败路线的边界

- 不继承 CHORM 的类别无关视觉位移，也不在 CHORM 上继续调参。
- 不继承 RBD、BRVM、RC-GDT、DCRA 或 DPEF 的失败叠加。
- 不使用 attention、类别专属参数、seen/unseen 专属参数或 gamma 校准。
- 不把 PSE-X2/CLIP-A-self 改名后声明为新模块。

## 当前证据边界

当前只有实现与合成张量机器测试，尚无正式训练指标。Owner 于 2026-08-16 明确
取消 pseudo-GZSL 前置门；RUN-001 将直接进行 150 seen 训练和 official test，
并标记为 `official-test-guided development`。
