# IDEA-0001：LaSt-ViT CLS 替换

```text
idea_id: IDEA-0001
status: candidate
source_type: hybrid
source_status: unverified
global_score: 55
current_version_score:
  v1: 55
idea_dir: idea_tree/ideas/IDEA-0001_lastvit_cls/
```

## 来源

代码注释声称参考 LaSt-ViT / Vision Transformers Need More Than Registers。
具体论文和官方代码尚未验证。

## 基于什么

- `v1`
- 冻结的 CLIP ViT-L/14@336px
- patch tokens
- base logits

## 假设

如果 pooled feature 仍能保持与 CLIP text space 对齐，那么用 part-aware patch pooled CLS
替换或融合 CLIP CLS，可能提升细粒度识别。

## 版本评分

| 版本 | 分数 | 适用性 | 理由 |
|---|---:|---|---|
| `v1` | 55 | needs_adaptation | 可能有用，但风险较高，因为 v1 依赖 CLIP-space alignment。 |

## 阻塞点

- 验证来源。
- 运行 shape 和 CLIP-alignment 检查。
