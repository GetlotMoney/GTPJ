# 实现说明

- `rcdp_model.py`：同角色 rival 搜索、八个角色独立低秩映射、逐角色单位范数上限、等权贡献和统一类别原型。
- `train.py`：100/50 类不重叠验证选择 epoch；150 类从零重训；checkpoint 后 official test 单次评估。
- RCDP 相对 RPR 的唯一核心变化：输入位移从类内 `t[c,r]-mean[c]` 改为跨类别同角色 `t[c,r]-t[j*,r]`。
- RCDP 相对 CLIP-A-self：不存在同类别句子之间的 Q/K/V self-attention，也不学习句子选择权重。
