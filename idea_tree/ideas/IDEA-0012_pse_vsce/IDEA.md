# IDEA-0012：PSE + VSCE 双向句子区域匹配

```text
idea_id: IDEA-0012
title: PSE + VSCE 双向句子区域匹配
status: rejected
source_type: user
source_ref: owner:2026-08-10:8句PSE+VSCE实验B
source_status: local_heuristic
base_version: v5
linked_experiment: V5-INNOVATION-010
```

## 核心想法

用同一张 8 句 × 图像全局/Top-K 区域匹配表，同时生成句子权重和局部区域权重，检验统一句子—区域匹配是否优于实验 A。

8 句话固定为：6 个局部部位、1 个独特判别特征、1 个全局描述。

## 实验结果

对应实验：`experiments/v5/innovation/INNOVATION-010_pse_vsce/`。

RUN-001 完成并判定为 reject：

```text
U=47.043979
S=78.809130
H=58.917815
ZS=75.780660
```

## 结论

该路线不保留。它相比实验 A 没有提升 H，也显著低于 V5 参考。下一步不继续在旧 V5 模块堆交互，而是做干净 V6 候选。
