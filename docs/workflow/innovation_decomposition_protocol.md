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
