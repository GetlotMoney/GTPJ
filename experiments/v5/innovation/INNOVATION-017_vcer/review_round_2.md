# VCER 代码审核：第 2 轮

```text
round: 2
reviewer_id: /root/vcer_review_round2
reviewed_code_id:
  vcer.py: 143dc00f92383012bfe0c797391dbf6a6e170057f4e3484765e2f8893a7dc720
  tests/test_v5_vcer.py: 7b1ba15f8c78be14292c5186e73cec873ef921b4960d4359a8a9f3728f787d1b
machine_test_ref: py_compile pass; tests.test_v5_vcer 12/12 pass; git diff --check pass
previous_round_ref: experiments/v5/innovation/INNOVATION-017_vcer/review_round_1.md
unresolved_blockers: 0
decision: pass
```

## reviewed_extra_files

- `implementation.md`
- `module_source.md`
- `framework_diagram.md`
- `review_round_1.md`
- `idea_tree/ideas/IDEA-0014_vcer/IDEA.md`
- `docs/workflow/protocols/code_interface_contract.md`
- 历史 `StrongRolePSE` 训练实现

## files_reviewed

Reviewer 逐行检查核心代码、12 项测试与上述额外文件，并用只读内存反例检查
候选重排、off 等价、角色干预和边界输入；未修改文件、未启动训练、未读取 official test。

## findings

- blocker：无。
- 非 tie 情况下，候选重排映射回全局类后的最大差为 `0`；off 对非单位 CLS 和
  任意候选顺序保持 bitwise 等价。
- unique 干预只改变角色权重，global 干预只改变前景项，local 干预只改变角色
  权重与 patch margin；冻结底分和 rival 均不变。
- seen/unseen 没有参数或公式分叉；视觉输入 detach；辅助 loss 权重为零时不计算、不贡献。

## Runner 接入期非阻断边界

1. 精确 tie 时 `topk` 会按候选位置破平局；当前协议必须保持固定 class order。
2. 当前核心允许空 batch 进入前置 shape 检查，训练损失会为 NaN；Runner 必须保证 `B>=1`。
3. 当前契约固定 float32；在明确实现 AMP 兼容前禁止直接 `model.half()`。
4. `training_loss.labels` 是全局类别 ID；历史 Runner 的局部 target 必须先显式转换，
   并在接入测试中覆盖非连续 `class_ids`。

## uncovered_scope

未覆盖真实 patch cache 显存/吞吐、GPU/AMP、Runner 标签适配、checkpoint、trial config、
pseudo-GZSL、正式 split 或任何 official-test 指标。
