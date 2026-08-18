# 模块来源与创新边界

RACE 来源于项目论文卡片中的同角色混淆证据与忠实加性解释缺口。它与 CLIP-A-self/PSE 的核心不同：不做句间 self-attention，不学习或移动 prototype，也不把 attention 权重当解释。

最近工作边界：DUET 已使用属性 hard-pair 对比；CLIP-Concepts 已提出加性概念解释。因此本实验只验证“固定八角色、完整语义全集冻结 rival、目标减同角色 rival 作为最终真实 logit 加数”的项目候选，不预先声称首次提出。
