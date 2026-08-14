# V5-INNOVATION-016 结果

```text
status: completed_stop_no_gain
decision: stop_no_gain
evidence_level: valid_single_run
not_confirmation_evidence: true
promotion_decision: rejected
```

## 结论

VSC-Loss 没有改善 TE-PSE：四项 official 指标与父实验的原始浮点数逐项完全相同，
`delta U/S/H/ZS = 0/0/0/0`。相对同次 B0，H 仍低 `0.462097`。因此本项按预注册门槛停止，
不进入 seed 17 或打乱类别对应负控制。

VSC 把最佳 validation CE 从父实验的 `2.493268013` 微降到 `2.493266582`，共享强度也只从
`0.498062223` 变到 `0.498069495`；这些微小变化没有改变任何 official 预测。它只能说明
训练目标被执行，不能说明共同分类能力提高。

## 完整比较

| 路径 | U | S | H | ZS |
|---|---:|---:|---:|---:|
| 同次 B0 | 63.037896 | 65.331149 | 64.164039 | 80.301231 |
| 父实验 TE-PSE | 63.251662 | 64.158678 | 63.701942 | 79.828095 |
| TE-PSE + VSC | 63.251662 | 64.158678 | 63.701942 | 79.828095 |
| VSC - 父实验 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| VSC - B0 | +0.213766 | -1.172471 | -0.462097 | -0.473136 |

机制诊断：`best_epoch=99`，`final_vsc_loss=2.213114023`，视觉到语义/语义到视觉损失分别为
`2.232152224/2.194075823`，最大加法分解误差为 `2.384186e-7`。

## 身份与证据

- run commit：`3e91d348abb82fab8c9046c73f55de0252a56ee7`
- parent TE-PSE commit：`b7f060afdd6d42baeee25b4d3068389085d88286`
- config SHA-256：`3b60554d3dd493d738f1de839205fcf670bfd7ab33f38c2f0b9ab4de6c645d24`
- Warehouse：`warehouse://runs/v5/innovation/V5-INNOVATION-016/RUN-001`
- `training.log`：`22de546a8e72fae2c3491f38eb888db0ac0f2efb6ba137c64942a6161abe3f40`
- `metrics.json`：`3c805306d7e157223c6279fa1211c2b188f90a28710e2c869bb38e3696d272ab`
- `result.yaml`：`70eb809b99904dca5b011f5a6f45f4d2b3b1f771c967b50ddca3792bbade1162`
- `model_best.pth`：`21fcefcebeb3c45ce1a1b8a211187ce7fc682b0beeb245add87e84e8cce260f8`

服务器没有生成 `artifact_manifest.json`，因此参数矩阵的 manifest 哈希保持空白，不补造证据。
