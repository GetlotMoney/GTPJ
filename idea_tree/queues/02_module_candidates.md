# 模块候选

这些候选模块来自当前 v1 代码中未启用或替代路径。它们还没有被选中实现，
对应开关也不属于 v1 baseline config。

这个队列是从 `idea_tree/INDEX.md` 派生出来的工作视图。不要把本文件当成排名事实来源；
排名更新应修改 `idea_tree/INDEX.md`、`idea_tree/idea_tree.json`，以及对应的
`ideas/IDEA-xxxx_slug/IDEA.md` 文件。

规则：任何 trial 开始前，来源必须被验证；或者 idea 必须明确标记为
`source_status: unknown` / `unverified`。当候选被选中时，它的开关只能加入
trial-local 的 `config.yaml`。

| Idea | 候选 | 主开关 | 来源状态 | 优先级 | 下一步 |
|---|---|---|---|---:|---|
| `IDEA-0001` | LaSt-ViT CLS 替换 | `use_lastvit_cls` | unverified | 0.55 | trial 前验证引用论文/来源。 |
| `IDEA-0002` | 动态局部分支门控与池化 | `gating_dynamic`, `weight_s2v_mode`, `pool_method=dmp`, `pool_dynamic` | unknown | 0.45 | 记录理由/来源后，再拆成单变量 trial。 |
| `IDEA-0003` | Cosine-only CrossModal 打分与 anchor loss | `score_mode=cosine_only`, anchor/distill/aux losses | unknown | 0.35 | 触碰主打分路径前，必须 review 来源/理由。 |
| `IDEA-0004` | AG-JEPA 邻居文本变体 | `use_ag_jepa_v2` | unknown | 0.40 | 判断这是本地想法还是论文支持。 |
| `IDEA-0005` | 反事实负文本 margin | `use_cf_neg_text` | unknown | 0.40 | trial 前记录来源或 local-heuristic 理由。 |
| `IDEA-0006` | 几何感知属性路由 | `use_geo_attr_routing` | unknown | 0.50 | 找来源支持，或标记为本地想法。 |
| `IDEA-0007` | 拓扑感知文本属性库 | `use_text_attr_reservoir` | unknown | 0.45 | 澄清来源，以及它和 topology loss 的关系。 |
| `IDEA-0008` | 属性-patch OT 对齐 | `use_attr_patch_ot` | unverified | 0.50 | 验证 OT/patch-attribute 的来源依据。 |
| `IDEA-0009` | 不确定性感知 MSDN gate | `use_uncertainty_msdn_gate` | unknown | 0.50 | 记录 confidence-gating 来源或本地理由。 |
| `IDEA-0010` | Seen-unseen 校准 loss | `lambda_cal`, `lambda_bias` | unknown | 0.30 | 选中前先找 GZSL calibration 参考。 |

不属于模块候选：

- `use_unzip`, `use_gpt`, `lambda_reg`, `lambda_con`：旧的空转 config key，代码中没有引用。
- `use_aug_cache`：runtime/cache 控制，不是模型模块。
- `use_amp`：runtime 加速控制，不是模型模块。
- `model_mode=clip_only/adapter_only`：消融控制，不是新模块。
