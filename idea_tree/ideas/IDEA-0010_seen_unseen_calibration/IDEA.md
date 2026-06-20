# IDEA-0010：Seen-unseen 校准 loss

```text
idea_id: IDEA-0010
status: candidate
source_type: observation
source_status: unknown
global_score: 30
current_version_score:
  v1: 30
idea_dir: idea_tree/ideas/IDEA-0010_seen_unseen_calibration/
```

## 来源

来源不明确。由未启用的 calibration 和 bias-margin losses 迁移而来。

## 基于什么

- `v1`
- base logits
- GZSL seen/unseen split

## 假设

显式 seen-unseen calibration 可能降低 generalized zero-shot evaluation 中的 seen-class bias。

## 版本评分

| 版本 | 分数 | 适用性 | 理由 |
|---|---:|---|---|
| `v1` | 30 | needs_adaptation | 应等 v1 baseline 确认后再做；优化目标应是 H，而不是只看 U。 |

## 阻塞点

- 找 GZSL calibration 参考。
- 定义基于 H 的决策规则。
