# Innovation Decomposition Protocol

创新按 hypothesis 和 implementation binding 管理，不能只按论文名管理。

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

一篇论文可以产生多个 hypotheses。同一个 hypothesis 如果接到不同代码路径或不同
forward/loss/eval binding，也可以产生多个 trials。

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

纯参数调优不能创建新的 method version `vX`；它只能在 confirmation 后成为
confirmed/reference config。

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

每个可运行 hypothesis 都应该有一个轻量 duplicate fingerprint：

```yaml
hypothesis_fingerprint:
  target_failure_mode:
  mechanism_family:
  expected_effect:
  attachment_family:
  eval_signal:
```

打开新 Trial 前，Coordinator 必须检查同一个 hypothesis 是否已经以其它名称存在。
