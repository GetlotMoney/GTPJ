# Innovation Decomposition Protocol

Innovation is managed by hypothesis and implementation binding, not by paper name alone.

## Hierarchy

```text
Paper
-> Claim / Mechanism
-> Hypothesis
-> Interpretation
-> Attachment Point
-> Trial
-> Attempt
```

## Boundary

```text
Hypothesis = scientific claim about why GZSL may improve.
Trial = hypothesis + interpretation + attachment point + implementation contract.
Attempt = parameter, seed, epoch, weight, top-k, or narrow runtime try inside one Trial.
```

One paper may produce multiple hypotheses. One hypothesis may produce multiple trials when it is attached to different code paths or forward/loss/eval bindings.

## Trial Split Rules

Open a new Trial when changing:

```text
scientific hypothesis
interpretation of the paper mechanism
attachment point
forward path
new loss mechanism
evaluation semantics
baseline-off contract
```

Stay inside the same Trial only for:

```text
parameter value
seed
epoch
batch size
loss weight
top-k
hidden size
other narrow config searches
```

Pure parameter tuning cannot create a new method version `vX`; it can only become a confirmed/reference config after confirmation.

## Innovation Source Rule

正式创新必须来自可追踪来源：

```text
idea_tree selected idea
paper-derived claim / mechanism
registered hypothesis
existing Trial follow-up hypothesis
owner-approved new hypothesis
```

如果一个 run 只是把当前 Trial 内已有的合法开关、gate mode 或权重组合起来，目的是测试
workflow、探针或快速筛方向，它只能登记为 `innovation_probe`，不是完整
`innovation / module trial`。`innovation_probe` 必须写明：

```yaml
source_type: existing_trial_switch_probe
parent_trial:
new_code_path: false
new_hypothesis: false unless explicitly stated
attachment_point:
why_this_probe:
```

完整 innovation workflow 需要先完成 idea/hypothesis 拆解，再进入 Review 0-3。

## Fingerprint

Every runnable hypothesis should have a lightweight duplicate fingerprint:

```yaml
hypothesis_fingerprint:
  target_failure_mode:
  mechanism_family:
  expected_effect:
  attachment_family:
  eval_signal:
```

Before opening a new Trial, Coordinator checks whether the same hypothesis already exists under another name.
