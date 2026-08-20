# IDEA-0021：三组 Value 原型重参数化

```text
idea_id: IDEA-0021
title: TG-VPR-H1
status: validated_candidate
source_type: owner_derived_from_X2_diagnostics
source_ref: git+commit://5ff6ce31b31872e042dec14028dd49d028a05cd6/experiments/v5/tune/TUNE-005_tg_vpr_h1_multiseed/result.md
```

## 假设

将六个局部描述先组内平均，再与独特描述、整体描述形成三个平级语义组；使用无 Q/K、单个 768 维 Value 路径重参数化 seen 类原型，可以比 X2 提供更稳定的 GZSL H。

## 已有证据

- X2：`H=73.523304`。
- TG-VPR-H1 seeds 5/6/7/8：`73.709453 / 73.864640 / 74.019664 / 73.759312`。
- 四 seed 平均 `73.838267`，范围 `0.310211`；当前 best observed 为 seed 7 `H=74.019664`。

上述多 seed 结果是 `not_confirmation_evidence`，不自动形成 promotion。

证据提交：`5ff6ce31b31872e042dec14028dd49d028a05cd6`。原始产物：`warehouse://runs/tg-vpr-h1-multiseed-20260821/`。
