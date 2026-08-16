# VCER 代码审核：第 1 轮

```text
round: 1
reviewer_id: /root/vcer_review_round1
reviewed_code_id:
  vcer.py: 143dc00f92383012bfe0c797391dbf6a6e170057f4e3484765e2f8893a7dc720
  tests/test_v5_vcer.py: 7b1ba15f8c78be14292c5186e73cec873ef921b4960d4359a8a9f3728f787d1b
machine_test_ref: py_compile pass; tests.test_v5_vcer 12/12 pass; git diff --check pass
unresolved_blockers: 0
decision: pass
```

## reviewed_extra_files

- `implementation.md`
- `module_source.md`
- `framework_diagram.md`
- `idea_tree/ideas/IDEA-0014_vcer/IDEA.md`
- `docs/workflow/protocols/code_interface_contract.md`
- 历史 `StrongRolePSE.prototypes/logits` 相关实现

## files_reviewed

Reviewer 逐行检查核心代码、12 项测试和上述接口说明；全程只读，未修改文件、
未启动训练、未读取 official test。

## 发现与修复闭环

1. 初版把六个角色整体一起置换，最终求和近似不变。修复为
   `role_evidence_permutation`：只错配 unique 路由权重与六路视觉证据。
2. 初版把 patch 插入 `logits` 第二位置，破坏旧 X2 调用。修复后保留
   `logits(image_features, class_ids, *, patch_features=...)`。
3. 初版因果 loss 没有独立关闭权重。修复后 VCER-off 只剩 X2 CE，两个辅助
   loss 权重为零时均精确不计算、不贡献。
4. 初版再次归一化 X2 最终原型，反例的 off logits 最大漂移
   `4.7683716e-7`。修复为验证 float32/单位范数后 clone 原值，并由构造器外
   原型独立验证 bitwise 等价。
5. image 与 patch 已强制 detach，梯度只进入共享低秩投影。

## uncovered_scope

尚未接入 Runner，因此未覆盖真实 patch cache 显存/吞吐、正式 split 绑定、
checkpoint 装载、trial config 默认关闭和 pseudo-GZSL 指标。
