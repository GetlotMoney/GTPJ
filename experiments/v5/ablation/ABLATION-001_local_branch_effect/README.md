# V5-ABLATION-001：局部分支效果

```yaml
framework: FRAMEWORK-V5
status: planned
legacy_ref: codex/attempt019-local-ablation#ATTEMPT-019@954851b0d2dfd2d23f1efca10ba1bf142b3a6d68
parameter_matrix: PARAMETER_MATRIX.md
```

`MODEL-V5-TEMPLATE-V1` 已冻结，本实验已经绑定到母版提交
`2f5fa5e631ef82658d4bac587cdfd17f3534cb35`，独立实验分支为
`exp/v5/ablation/ablation-001-local-branch-effect`。旧 `ATTEMPT-019` 只保留为规划来源，代码不继承。

15 行参数表已经用新母版重新计算基线哈希和参数指纹，但仍全部是 `planned`，不会启动 Runner。实验代码还要在独立分支实现并审核；实现完成后生成真实配置快照，再把要运行的行冻结。

其中 L0 只是把局部分数权重设为 0，L3 才是代码级完全移除 FGVD、BVSA、ICSA、SGMP 和对应损失。两者必须分别报告，不能把 L0 冒充“完全去掉局部分支”。
