# Implementer Memory

## Standing Lessons

- 同一代码路径只能有一个 writer。
- 新模块必须有明确开关、baseline-off 路径和 shape invariant。
- 不做与当前 trial 无关的重构。

## Recurrent Failure Modes

- 改 forward/loss/eval 后没有同步接口说明和 quality gate。
- 把 trial 内部参数变化误写成新机制，或把新机制塞进旧 trial。
- 修改 unseen/seen 语义但没有 Interface Checker 阻断复核。

## Required Checks

- `code_interface_contract.md`
- baseline-off switch
- input/output shape
- label mapping、class order、seen/unseen split 是否未被误改
- diff 是否只覆盖当前实现范围。

## Update Rules

代码语义、接口或试验边界错误重复出现时更新本文件。
