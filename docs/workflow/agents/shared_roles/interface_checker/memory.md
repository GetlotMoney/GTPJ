# Interface Checker Memory

## Standing Lessons

- label mapping、seen/unseen split、class order、logits shape、metric semantics 不清楚时必须阻断。
- GZSL 中 unseen 是否参与 forward、loss 或 topology 必须明说。
- 训练监督和评估类别范围要分开检查。

## Recurrent Failure Modes

- 把 unseen 文本原型进入 forward 误认为 unseen label 参与监督。
- CE、topology、anchor 等 loss 的类别范围没有写清。
- logits shape 和 class order 没有和 evaluator 对齐。

## Required Checks

- train/eval split
- label mapping
- class order
- logits shape
- metric calculation
- loss 输入类别范围。

## Update Rules

任何接口语义争议或 GZSL 合规性争议复发时更新本文件。
