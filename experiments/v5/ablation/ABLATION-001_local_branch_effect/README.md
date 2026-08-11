# V5-ABLATION-001：局部分支真实贡献

```text
framework: FRAMEWORK-V5
status: completed_reviewed
base_template: MODEL-V5-TEMPLATE-V1
base_commit: 2f5fa5e631ef82658d4bac587cdfd17f3534cb35
experiment_branch: exp/v5/ablation/ablation-001-local-branch-effect
```

## 比较的问题

本实验比较完整 V5 与彻底移除局部子系统后的版本。去掉的内容包括 FGVD、BVSA、SGMP、局部融合，以及依赖局部特征的辅助损失；PSE、ICSA、数据划分、类别顺序、训练轮数和评估口径保持不变。

每组使用 seed 5、17、29，按相同 seed 成对比较。

## 结果

| 指标 | 完整 V5 | 去局部分支 | 差值（完整减去局部） |
|---|---:|---:|---:|
| U | 72.03 | 71.48 | +0.55 |
| S | 76.32 | 76.77 | -0.45 |
| H | 74.11 | 74.03 | +0.08 |
| ZS | 81.28 | 81.27 | +0.01 |

三个 seed 的 H 差值为 `+0.25/-0.09/+0.09`。完整版本训练约慢 `1.69 倍`，最佳模型约大 `6.16 倍`。

## 结论

局部分支会改变 U/S 平衡，但没有证明它稳定提高最终 H。因此当前不把它作为论文主性能贡献；后续模块消融优先从干净无局部版本建立独立实验。

详细指标见 `result.md`，逐任务参数和外部证据位置见 `PARAMETER_MATRIX.md`。
