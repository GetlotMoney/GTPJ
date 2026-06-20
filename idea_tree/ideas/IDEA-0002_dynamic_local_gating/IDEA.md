# IDEA-0002：动态局部分支门控与池化

```text
idea_id: IDEA-0002
status: candidate
source_type: observation
source_status: unknown
global_score: 45
current_version_score:
  v1: 45
idea_dir: idea_tree/ideas/IDEA-0002_dynamic_local_gating/
```

## 来源

来源不明确。由未启用的代码开关迁移而来。

## 基于什么

- `v1`
- base logits
- local_score
- score_s2v / score_v2s

## 假设

输入相关的 gating 可能降低局部分支在简单样本上的有害影响，同时保留困难样本所需的局部证据。

## 版本评分

| 版本 | 分数 | 适用性 | 理由 |
|---|---:|---|---|
| `v1` | 45 | needs_adaptation | 只有拆成单变量 trial 才有解释性；多个 gate 同时变化会难以判断。 |

## 阻塞点

- 记录来源或本地理由。
- 把 dynamic gate、branch weight 和 pooling 拆成独立 idea 或 trial。
