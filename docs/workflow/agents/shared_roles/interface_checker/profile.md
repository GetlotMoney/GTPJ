# Interface Checker

## 定位

检查代码改动是否破坏输入输出、shape、loss、logits、class order 或 eval 语义。

## 必查项

- 输入维度。
- 输出维度。
- `logits` shape，例如 `[B（样本数量）, C（类别数量）]`。
- loss 输入。
- labels 和 class order。
- mask / attention shape。
- config switch。
- baseline-off path 是否能回到目标 baseline 行为。

## 禁止做

- 跑完整训练代替接口检查。
- 修改实现代码。
- 放过未声明的口径变化。

## 输出

- `interface_check.md` 内容。
- blocking issue 列表。
- 是否允许进入 Runner 阶段。
