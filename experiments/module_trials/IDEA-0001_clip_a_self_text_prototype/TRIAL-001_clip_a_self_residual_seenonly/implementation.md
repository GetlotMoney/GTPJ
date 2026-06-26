# 实现记录

参考契约：

```text
docs/workflow/code_interface_contract.md
```

## 新模块

CLIP-A-self text prototype adapter。

本 trial 把 v1 的 seen-class MLP text adapter 替换为句子级 self-attention adapter。输入不是已经平均后的 `[C（类别数量）, D（文本特征维度）]`，而是每类 GPT/VDT 描述句的 CLIP text features：

```text
[C（类别数量）, M（每类句子数量）, D（文本特征维度）]
```

TRIAL-001 保留外层 prototype residual，并默认不让 unseen 类经过可训练 adapter。

## 基于什么

- base version: `v1`
- base code tag: `v1`
- source idea: `idea_tree/ideas/IDEA-0001_clip_a_self_text_prototype/IDEA.md`
- paper/code source: `https://github.com/mayug/VDT-Adapter`

## 接入点

| 项目 | 值 |
|---|---|
| File | `train_GTPJ_CUB.py` |
| Class/function | `_encode_description_sentences`, `GTPJ(...)` init call |
| 接入前/后 | GPT/VDT descriptions encoded before model init |
| Consumes | `cub_gpt55.pt` descriptions, `class_text_embeds`, `dataloader.seenclasses`, `dataloader.unseenclasses` |
| Produces | `seen_sentence_embeds`, `unseen_sentence_embeds` |

| 项目 | 值 |
|---|---|
| File | `model/MyModel.py` |
| Class/function | `CLIPASelfAdapter`, `GTPJ.get_adapted_seen_text`, `GTPJ._make_all_text` |
| 接入前/后 | Replaces seen text adapter path only when `use_clip_a_self: true` |
| Consumes | `seen_sentence_embeds`, optional `unseen_sentence_embeds` |
| Produces | adapted seen text prototype `[150, 768]`; all-class text matrix `[200, 768]` |

## Input Contract（输入契约）

| 名称 | Shape | Dtype | Device | 含义 | Gradients |
|---|---|---|---|---|---|
| `seen_sentence_embeds` | `[150（seen 类数量）, M（每类句子数量）, 768（文本特征维度）]` | float32 | config device | seen 类 GPT/VDT 句子级 CLIP text features | no |
| `unseen_sentence_embeds` | `[50（unseen 类数量）, M（每类句子数量）, 768（文本特征维度）]` | float32 | config device | unseen 类 GPT/VDT 句子级 CLIP text features；TRIAL-001 默认不通过 adapter | no |
| `clip_features` | `[B（图片/样本数量）, 577（CLS+patch token 数量）, 768（视觉特征维度）]` 或兼容旧 CLS path | float32/bfloat16 | config device | CLIP visual features | yes |

## Output Contract（输出契约）

| 名称 | Shape | Dtype | Device | 含义 | 是否替换已有变量 |
|---|---|---|---|---|---|
| `adapted_seen_text` | `[150（seen 类数量）, 768（文本特征维度）]` | float32/autocast dtype | model device | CLIP-A-self 聚合后的 seen 文本 prototype | 替换 baseline MLP adapted seen text |
| `all_text` | `[200（总类别数量）, 768（文本特征维度）]` | float32/autocast dtype | model device | seen adapted + unseen raw text matrix | 保持原变量语义 |
| `logits_200` | `[B（图片/样本数量）, 200（总类别数量）]` | float32/autocast dtype | model device | 全类 GZSL logits | 不改变语义 |

## Shape Invariants（形状不变量）

- [x] Batch dimension 保持不变。
- [x] Class dimension 保持不变。
- [x] Logits shape 保持 `[B（图片/样本数量）, C（类别数量）]`。
- [x] Visual/text embedding dimensions 仍与 scorer 兼容。
- [x] Seen/unseen 类别顺序不变。
- [x] 没有引入意外 broadcasting。

## 配置开关

```text
switch: use_clip_a_self
default: false in code path unless explicitly set by trial config
trial config path: experiments/module_trials/IDEA-0001_clip_a_self_text_prototype/TRIAL-001_clip_a_self_residual_seenonly/config.yaml
base config affected: no
trial values:
  use_clip_a_self: true
  clip_a_self_apply_unseen: false
  clip_a_self_heads: 1
  clip_a_self_dropout: 0.5
  clip_a_self_inner_ratio: 0.5
  clip_a_self_outer_ratio: 0.2
```

## Baseline-Off Path（基线关闭路径）

`use_clip_a_self=false` 时：

- `train_GTPJ_CUB.py` 继续只生成 averaged text embeddings `[200, 768]`。
- `GTPJ.__init__` 不实例化 `CLIPASelfAdapter`。
- `GTPJ.get_adapted_seen_text()` 继续使用 v1 MLP `Adapter`。
- `seen_text_embeds`、`unseen_text_embeds`、`all_text`、`logits_200` 和 loss/eval path 保持 v1 语义。

## Loss Contract（Loss 契约）

```text
new loss: none
lambda key: none
lambda=0 behavior: not applicable
normalization/reduction changes: none
```

L2SP 边界：`lambda_l2sp` 不是 TRIAL-001 的实验变量；当前仍由 baseline guard 拦截非零值，只作为后续 prototype drift 风险下的 ablation/anchoring question。

## Evaluation Contract（评估契约）

```text
eval path changed: no
logits shape: [B（图片/样本数量）, 200（总类别数量）]
class order: unchanged; uses dataloader.seenclasses/unseenclasses
metric calculation: unchanged; tools.helper_func.eval_zs_gzsl
```

## Checkpoint Contract（Checkpoint 契约）

```text
new state_dict keys: clip_a_self_adapter.*, seen_sentence_embeds, optional unseen_sentence_embeds when use_clip_a_self=true
old checkpoint load behavior: old v1 checkpoints are not expected to strict-load into this trial model without strict=False
missing/unexpected keys: expected for CLIP-A-self trial parameters
```

## 风险

- Seen-only CE may overfit the adapter toward seen classes.
- Unseen prototypes remain raw sentence means in TRIAL-001 to reduce prototype drift risk.
- Sentence-level cache must not replace the baseline averaged cache unless `use_clip_a_self=true`.
- A result is invalid if class order, seen/unseen split, label mapping, logits shape, or metric semantics drift.

## Minimum Verification（最低验证）

- [x] Switch-off forward pass。
- [x] Switch-on forward pass。
- [x] Logits shape check。
- [x] Loss scalar 和 backward check。
- [ ] Evaluation 输出 class-count 检查。
- [x] Base config files 没有变化。

## 验证命令

```powershell
python -m py_compile train_GTPJ_CUB.py model\MyModel.py
python workflow\gtpj_workflow.py validate
python workflow\gtpj_workflow.py audit-boundary
python -m unittest tests.test_gtpj_workflow -v
```

## 训练前接口预检

已完成小 batch dry probe：

```text
shape_probe_ok
switch_off_max_abs_diff: 0.0
switch_on_logits: [2（图片/样本数量）, 150（seen 类数量）]
switch_on_logits_200: [2（图片/样本数量）, 200（总类别数量）]
loss_keys: loss, loss_CE, loss_consist, loss_jepa, loss_jepa_neg, loss_msdn, loss_msdn_gate, loss_topo
```

解释：

- `use_clip_a_self=false` 时，与未接入句级输入的 baseline-off 路径完全一致。
- `use_clip_a_self=true` 时，训练 logits 仍只切 seen 类，`logits_200` 仍保留全 200 类。
- loss key 集合未新增或删除。
- backward 能把梯度传到 `clip_a_self_adapter`。
