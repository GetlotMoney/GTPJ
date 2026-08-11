# IDEA-0011：图像条件 PSE 选句

```text
idea_id: IDEA-0011
title: 图像条件 PSE 选句
status: rejected
source_type: user
source_ref: owner:2026-08-10:8句图像条件PSE实验A
source_status: local_heuristic
base_version: v5
linked_experiment: V5-INNOVATION-009
```

## 核心想法

保留 PSE 和原局部分支，只让全局图像对 8 句话生成句子权重，检验“全局选句”是否足够。

8 句话固定为：6 个局部部位、1 个独特判别特征、1 个全局描述。

## 实验结果

对应实验：`experiments/v5/innovation/INNOVATION-009_image_conditioned_pse/`。

RUN-002 完成并判定为 reject：

```text
U=47.921973
S=78.128189
H=59.405826
ZS=76.428151
```

## 结论

该路线不保留。它仍混有 V5 的频域 Top-K、BVSA 和旧损失，无法证明“全局选句”本身有效，也暴露了旧模块可能干扰新框架判断的问题。
