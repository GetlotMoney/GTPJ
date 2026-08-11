# IDEA-0013：干净 V6 框架候选

```text
idea_id: IDEA-0013
title: 干净 V6 框架候选
status: selected
source_type: user
source_ref: owner:2026-08-11:删除旧模块和旧损失，验证干净新框架
source_status: local_heuristic
base_version: v5
linked_experiment: V5-INNOVATION-011
```

## 核心问题

009/010 都在保留旧 V5 模块和旧损失的情况下明显掉点。现在要回答的是：新交互框架本身是否合理，还是被频域解耦、拓扑损失、旧局部分支和辅助损失干扰了。

## 干净框架原则

- 8 句话固定解释为：6 个局部部位、1 个独特判别特征、1 个全局描述。
- 删除频域解耦 / Top-K、ICSA、BVSA、SGMP、BMDD、拓扑损失和全局/局部辅助损失。
- 只保留 CLIP、8句文本编码、PSE、句子—区域匹配、最终融合分数和主分类损失。
- 相同数据划分、CLIP 骨干、seed、epoch 和 U/S/H/ZS 评估口径。

## 登记方式

先登记为 `V5-INNOVATION-011_clean_v6_candidate`。只有完成实现、训练、重复验证并通过 promotion 判断后，才注册正式 `FRAMEWORK-V6` 和对应 tag。

## 当前状态

planned。尚未实现，尚未训练，不能作为 V6 正式结果引用。
