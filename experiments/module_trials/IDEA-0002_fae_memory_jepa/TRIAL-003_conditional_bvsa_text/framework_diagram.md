# Framework Diagram: IDEA-0002 / TRIAL-003

```text
trial_id: TRIAL-003
idea_id: IDEA-0002
base_version: v3
code_path: conditional BVSA text input
code_vs_intent: all_text_cond is now the direct BVSA text input when bvsa_text_mode=conditional.
```

## Shape Legend

```text
B = batch size / number of images
K = selected patch count, 32 when lastvit_select_k=32
C = class count, 200 on CUB
D_clip = CLIP feature dimension, 768
D = transformer hidden dimension, 512
```

## Main Forward And Loss Flow

```mermaid
flowchart LR
  In["clip_features [B,577,768]"] --> Split["GTPJ.forward: cls_token + patches"]
  Split --> Text0["CLIP-A-self adapter"]
  Text0 --> AllText["all_text [C,768]"]
  Split --> Meta["meta_net(cls_token)"]
  AllText --> Cond["all_text_cond [B,C,768]"]
  Meta --> Cond

  Cond --> Base["base_logits [B,C]"]
  Cond --> BVSA["CrossModalTransformer.forward text input<br/>bvsa_text_mode=conditional"]

  Split --> Patches["patches / selected_patches [B,K,768]"]
  Patches --> EmbedCV["embed_cv -> patch_z [B,K,512]"]
  EmbedCV --> FAE["FAE -> jepa_memory [B,K,512]"]
  FAE --> BVSA

  BVSA --> V2S["decoder_v2s<br/>text target + visual memory"]
  BVSA --> S2V["decoder_s2v<br/>visual target + text memory"]
  V2S --> Local["local_score [B,C]"]
  S2V --> Local
  Base --> Fuse["logits_200 = base_logits + 0.3 * local_score"]
  Local --> Fuse
  Fuse --> CE["loss_CE"]

  Base --> Cons["loss_consist<br/>base_logits.detach() teacher"]
  Local --> Cons

  FAE --> AG["AG-JEPA context<br/>mean keep jepa_memory"]
  Cond --> AGText["positive / negative conditional text"]
  AGText --> AG
  AG --> LJ["loss_jepa + loss_jepa_neg"]
```

## Variable Glossary

| Variable | Produced by | Consumed by | Shape | Meaning | Gradient boundary | Train/eval difference |
|---|---|---|---|---|---|---|
| `all_text` | `_make_all_text` | baseline-off BVSA path, conditional text construction | `[C,768]` where `C` is class count | Shared CLIP-A-self adapted class prototypes | gradients reach text adapter where enabled | same train/eval |
| `all_text_cond` | `all_text + conditional_text_ratio * meta_net(cls_token)` for seen classes | `base_logits`, AG-JEPA text, and BVSA when `bvsa_text_mode=conditional` | `[B,C,768]` where `B` is batch size | Per-image conditional class prototypes | gradients reach `meta_net` and text adapter | requires CLS token |
| `txt_batch` | `CrossModalTransformer.embed_text(text)` | `decoder_v2s`, `decoder_s2v`, local score | `[B,C,512]` in conditional mode | BVSA text memory/target for each image | no detach | same shape in train/eval if CLS exists |
| `local_score` | BVSA decoders | final fusion, consistency loss | `[B,C]` | Local visual-semantic class score | gradients reach BVSA, FAE, and conditional text path | train slices seen logits after fusion |
| `base_logits` | cosine of visual CLS and `all_text_cond` | final fusion, consistency teacher | `[B,C]` | Global class score | detached inside `loss_consist` teacher path | same train/eval before seen slicing |

## Method Glossary

| Method/module | Code location | Input | Output | Responsibility | Switch |
|---|---|---|---|---|---|
| `GTPJ.forward` | `model/MyModel.py` | `clip_features` | logits package | Builds class text, chooses BVSA text, fuses scores | `bvsa_text_mode` |
| `CrossModalTransformer.forward` | `model/MyModel.py` | patches plus text `[C,768]` or `[B,C,768]` | `local_score`, `score_v2s`, `score_s2v`, JEPA tensors | Computes BVSA local branch | input shape driven by `bvsa_text_mode` |
| `decoder_v2s` | `CrossModalTransformer` | text target, visual memory | class-wise text-aligned features | Visual-to-semantic branch | always on |
| `decoder_s2v` | `CrossModalTransformer` | visual target, text memory | patch-wise visual-aligned features | Semantic-to-visual branch | always on |

## Baseline-Off Behavior

```text
bvsa_text_mode=adapted -> old v3 behavior:
  CrossModalTransformer receives all_text [C,768].

bvsa_text_mode=conditional -> TRIAL-003 behavior:
  CrossModalTransformer receives all_text_cond [B,C,768].
```
